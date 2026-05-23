import time
from typing import Dict, Set
from core.observability.logger import dgm_logger

class DeadlockDetector:
    def __init__(self):
        self.wait_graph: Dict[str, str] = {} # agent_id -> waiting_for_agent_id

    def register_wait(self, agent_id: str, waiting_for: str) -> bool:
        """Requirement 7: Snapshot first, recover second."""
        self.wait_graph[agent_id] = waiting_for
        if self._has_cycle(agent_id):
            dgm_logger.critical(f"DeadlockDetector: DEADLOCK DETECTED involving agent {agent_id}!")
            self._snapshot_state_for_recovery()
            return True
        return False

    def unregister_wait(self, agent_id: str):
        if agent_id in self.wait_graph:
            del self.wait_graph[agent_id]

    def _snapshot_state_for_recovery(self):
        dgm_logger.info("DeadlockDetector: Creating safety snapshot of wait graph before recovery...")
        # In a real system, we'd persist self.wait_graph to AndreOS or DB
        snapshot = str(self.wait_graph)
        dgm_logger.debug(f"DeadlockDetector: Snapshot content: {snapshot}")

    def _has_cycle(self, start_id: str) -> bool:
        visited = set()
        curr = start_id
        while curr in self.wait_graph:
            if curr in visited:
                return True
            visited.add(curr)
            curr = self.wait_graph[curr]
            if curr == start_id:
                return True
        return False
