#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Create / manage snapshots of my ZFS pool, in addition to replication.
"""

from typing import List, Any, Dict, Union, ContextManager
from pykwalify.core import Core
from weir import zfs

import libvirt as lv
#import libzfs_core as zfs  ## Only supports Python 2.
import multiprocess
import os
import sys
import yaml
import time


__all__ = [
    'ROLibvirtConnection',
    'PoolSnapshotManager'
]

schemaFile = '../schema.yml'

_ValRetType = List[Dict[str, Union[str, List[Dict[str, str]], List[str]]]]


class ROLibvirtConnection(ContextManager['ROLibvirtConnection']):
    """
    RO-CM / wrapper for libvirt to make local system calls and extract 
    information about domains.
    """
    def __init__(self, qemu: str ='qemu:///system') -> None:
        self.qemu = qemu

    def __enter__(self) -> 'ROLibvirtConnection':
        """
        Set up the connection to libvirt; this will raise its own exception
        should the connection not be possible.
        """
        self.conn = lv.openReadOnly(self.qemu)
        return self

    def getDomains(self) -> List[str]:
        """
        Get all domains (equivalent to `virsh list --all`, in a way)
        """
        return list(map(lambda d: d.name(), self.conn.listAllDomains()))

    def getActiveDomains(self) -> List[str]:
        """
        Get a list of only active domains.
        """
        runningDomains = []

        # To get the state codes, see `virDomainState` enum defined in
        # https://libvirt.org/html/libvirt-libvirt-domain.html
        for dom in self.getDomains():
            if self.conn.lookupByName(dom).state()[0] == 1:
                runningDomains.append(dom)

        return runningDomains

    def getInactiveDomains(self) -> List[str]:
        """
        Opposite of `getActiveDomains`.
        """
        return list(set(self.getDomains()) - set(self.getActiveDomains()))

    def __exit__(self, *args: Any) -> None:
        self.close()

    def close(self) -> None:
        self.conn.close()


class PoolSnapshotManager:
    """
    Provide a nice interface to the pool snapshots and ZFS
    """
    def __init__(self, domains: List[str], activeDomains: List[str] =None,
                 globalRetention: int =75) -> None:
        self.pool = pool
        self.retention = globalRetention
        self.domains = domains
        self.activeDomains = activeDomains

    def setup(self, yamlConfig: str) -> 'PoolSnapshotManager':
        """
        Set up this pool manager instance. This should be the first thing
        that's called.
        """
        # Aquire a validated YAML configuration for this snapshot manager
        # instance.
        self._config = self.acquireYAMLConfig(
            configFile=YAMLConfig, 
            validationFile=schemaFile,
            domains=self.domains
        )

        # Extract the pool configuration that matches this instance.
        for pool in self._config:
            if pool['name'] == self.pool:
                self._config = pool
        else:
            raise ValueError(f'Requested pool `{self.pool}` is not defined.')

        # Parse out the information so this class can handle it as the schema
        # outlines.
        self.regularDatasets = self._config['datasets']
        self.VMDatasets = self._config['VMs']
        self.retention = self._config['retention']

        return self

    def destroy(self, snapshot: str) -> None:
        """
        Destroy a snapshot from the designated pool. (Irreversible.)
        """
        snap = zfs.ZFSSnapshot(snapshot)

        # TODO: Interface is incomplete at this time, I believe. I've cloned 
        # the codebase on GitHub and I'm going to add some of this 
        # functionality for the interface.
        if not snapshot.getpropval('clones'):
            snap.destroy(force=False)

    def clone(self, snapshot: str, newDatasetName: str) -> None:
        """
        Clone a snapshot to the designated dataset name.
        """
        snap = zfs.ZFSSnapshot(snapshot)
        snap.clone(name=newDatasetName, force=False)

    def snapshot(self, dataset: str) -> None:
        """
        Snapshot a dataset, respecting whether this dataset contains an 
        (in)active VM.
        """
        snap = zfs.ZFSSnapshot(dataset)

        # If this fails, the reason why is usually straightforward enough.
        snap.snapshot(snapname=f'{int(time.time())}')

    def runRetention(self, dataset: str) -> List[str]:
        """
        Action to destroy snapshots on a dataset (from earliest
        to latest) until the number falls under `self.retention`.
        """
        snapList = zfs.ZFSSnapshot(dataset)
        snapCount = len(snapList.snapshots())
        if snapCount > self.retention:
            toDestroy = snapCount - self.retention
            destroyedSnapshots = list(map(lambda s: s.name, snapList[:toDestroy]))
        
            # Now destroy the necessary snapshots.
            for snapshot in snapList[:toDestroy]:
                self.destroy(snapshot)

            return destroyedSnapshots
        return []

    def snapshotDatasets(self) -> None:
        """
        Action to snapshot datasets of both VMs and regular datasets.
        """
        for dataset in self.regularDatasets:
            self.snapshot(dataset)
            self.runRetention(dataset)

        for VM in self.VMDatasets:
            dataset = zfs.ZFSDataset(VM['dataset'])
            mountpoint = dataset.getpropval('mountpoint')
            if VM['domain'] in self.activeDomains:
                open(f'{mountpoint}/on').close()
            else:
                open(f'{mountpoint}/off').close()
            self.runRetention(dataset.name)

    @staticmethod
    def acquireYAMLConfig(configFile: str, 
                      validationFile: str, 
                      domains: List[str]) -> _ValRetType:
        """
        Parse YAML config file and return dictionary.
        """
        # Validate the input file before reading it from file with `yaml`.
        c = Core(source_file=configFile, schema_files=[validationFile],
                strict_rule_validation=True)

        # If there's an exception, then call it out to the user.
        c.validate(raise_exception=True)

        # Proceed with opening and parsing the file, now that its structure /
        # schema has been validated.
        with open(configFile, 'r') as y:
            parsed = yaml.safe_load(y)

        class InvalidDomainRequest(KeyError):
            pass

        # Validate the requested domains against a master list.
        for pool in parsed:
            if pool['name'] not in domains:
                raise InvalidDomainRequest(f'Invalid domain: {pool["name"]}')

        return parsed
