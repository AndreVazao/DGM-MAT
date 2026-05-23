from typing import List, Callable, Any
from core.observability.logger import dgm_logger

class RepairChain:
    def __init__(self):
        self.steps: List[Callable[[], bool]] = []

    def add_step(self, step_fn: Callable[[], bool]):
        self.steps.append(step_fn)

    def execute(self) -> bool:
        for i, step in enumerate(self.steps):
            dgm_logger.info(f"Executing repair step {i+1}/{len(self.steps)}")
            if not step():
                dgm_logger.error(f"Repair step {i+1} failed.")
                return False
        return True
