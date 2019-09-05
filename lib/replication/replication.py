"""
Manage zpool replication to a secondary pool.
"""

from .rollZFS import ManagePoolSnapshots


__all__ = [
    'ZFSReplicator'
]


class ZFSReplicator(ManagePoolSnapshots):
    """
    Replicate my pool to another host (In my case, a U-NAS).
    """
    def __init__(self, pool: str, secondaryRetention: int, host: str,
                 destinationPool: str) -> None:
        ManageSnapshots.__init__(self, pool)
        self._secondaryReplicationRetention = secondaryRetention
        self._destinationHost = host
        self._destinationPool = destinationPool

        # Grab the YAML config so we know which datasets require replication.
        self.setup()

    def send(self, snapshot: str) -> None:
        """
        Send a snapshot to the destination pool.
        """

    def _fetchRemoteSnapshots(self, dataset: str) -> List[str]:
        """
        Fetch a list of remote snapshot names on a dataset. Returns empty `[]`
        if the dataset does not exist on the remote host.
        """

    def safeDestroy(self, snapshot: str) -> None:
        """
        Since this subclass has the ability to reach out to other pools, we can
        implement a safe check to ensure there's a duplicate of this snapshot
        or a later snapshot from this dataset in the designated remote pool.
        """

