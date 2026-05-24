from core.observability.logger import dgm_logger

class ExecutionMemory:
    """
    Persistent memory for execution history and lessons learned.
    """
    def __init__(self):
        self.logs = []

    def record_execution(self, execution_data: dict):
        dgm_logger.info("ExecutionMemory: Recording execution event")
        self.logs.append(execution_data)
