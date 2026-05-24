from core.observability.logger import dgm_logger

class RuntimeAffinity:
    """
    Determines if a task should run locally or in the cloud.
    """
    def get_execution_target(self, task_complexity: str):
        if task_complexity == "low":
            return "local"
        return "cloud"
