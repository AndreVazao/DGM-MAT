from typing import List
from core.governance.governance_models import ResourceSnapshot
from core.observability.logger import dgm_logger

class MemoryController:
    def __init__(self, limit_percent: float):
        self.limit_percent = limit_percent
        self.snapshots: List[ResourceSnapshot] = []

    def check_memory(self, snapshot: ResourceSnapshot):
        self.snapshots.append(snapshot)
        if len(self.snapshots) > 100:
            self.snapshots.pop(0)

        if snapshot.memory_percent > self.limit_percent:
            dgm_logger.warning(f"MemoryController: Memory usage {snapshot.memory_percent}% exceeds limit {self.limit_percent}%!")
            self._prune_memory()

    def _prune_memory(self):
        dgm_logger.info("MemoryController: Pruning non-critical caches and historical fragments...")
        # Implementation of pruning logic would go here
