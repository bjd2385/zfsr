## zfsretention

Just a simple module that manages local retention and secondary replication of ZFS snapshots.

Also, for VM datasets (that is to say, ZFS datasets that host VM disks), an indicator file is placed to inform whether the VM was activate at the time of snapshot. It is possible to find those points where the VM was active or inactive as follows --
```
$ find "$datasetMountPoint" -name "(on|off)"
```

# Install

Simply run
```
./build.sh
```
