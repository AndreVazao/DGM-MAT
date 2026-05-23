class DistributedMemory:
    def __init__(self):
        self.memory_snapshots = []

    def sync_snapshot(self, snapshot):
        self.memory_snapshots.append(snapshot)
