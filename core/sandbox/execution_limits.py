from core.observability.logger import dgm_logger

class ExecutionLimits:
    """Enforces resource quotas and limits on autonomous executions."""
    def __init__(self):
        self.max_cpu = 80
        self.max_memory_gb = 4

    def check_limits(self, usage: dict) -> bool:
        if usage.get("cpu", 0) > self.max_cpu:
            dgm_logger.warning("ExecutionLimits: CPU limit exceeded.")
            return False
        return True
