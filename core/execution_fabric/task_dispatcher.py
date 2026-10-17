from core.observability.logger import dgm_logger
from core.execution_fabric.autonomous_executor import AutonomousExecutor

class TaskDispatcher:
    """
    Dispatches tasks to specialized execution agents or engines.
    """
    def __init__(self):
        self.executor = AutonomousExecutor()

    def dispatch(self, task: dict):
        dgm_logger.info(f"TaskDispatcher: Dispatching task {task.get('id')}")
        return self.executor.execute_task(task)
