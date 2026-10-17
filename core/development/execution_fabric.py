from typing import List, Dict, Any
from core.observability.logger import dgm_logger

class ExecutionFabric:
    def __init__(self):
        self.active_tasks = []

    def dispatch(self, task: Dict[str, Any]):
        dgm_logger.info(f"Execution Fabric: Dispatching task {task.get('id')}...")
        self.active_tasks.append(task)
