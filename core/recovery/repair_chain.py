from typing import List, Callable
from core.observability.logger import dgm_logger


class RepairChain:
    def __init__(self):
        self.steps: List[Callable[[], bool]] = []

    def add_step(self, step_fn: Callable[[], bool]):
        self.steps.append(step_fn)

    def execute(self) -> bool:
        if not self.steps:
            dgm_logger.warning("RepairChain has no steps; recovery cannot be reported as successful.")
            return False

        for i, step in enumerate(self.steps):
            dgm_logger.info(f"Executing repair step {i+1}/{len(self.steps)}")
            try:
                if not step():
                    dgm_logger.error(f"Repair step {i+1} failed.")
                    return False
            except Exception as exc:
                dgm_logger.error(f"Repair step {i+1} raised an exception: {exc}")
                return False

        return True
