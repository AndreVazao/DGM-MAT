import psutil
from typing import Dict, Any
from core.observability.logger import dgm_logger

class ResourceGovernor:
    """
    Enforces resource budgets and prevents system overload.
    """
    def __init__(self, cpu_limit: float = 80.0, ram_limit: float = 85.0):
        self.cpu_limit = cpu_limit
        self.ram_limit = ram_limit
        self.throttled = False

    def check_budgets(self) -> bool:
        """
        Returns True if system is within budgets, False if throttling required.
        """
        cpu_usage = psutil.cpu_percent(interval=None)
        ram_usage = psutil.virtual_memory().percent

        if cpu_usage > self.cpu_limit or ram_usage > self.ram_limit:
            if not self.throttled:
                dgm_logger.warning(f"ResourceGovernor: Budget exceeded (CPU: {cpu_usage}%, RAM: {ram_usage}%). Throttling active.")
            self.throttled = True
            return False

        if self.throttled:
            dgm_logger.info("ResourceGovernor: Resource usage normalized. Throttling lifted.")

        self.throttled = False
        return True

    def health(self) -> Dict[str, Any]:
        return {
            "cpu_limit": self.cpu_limit,
            "ram_limit": self.ram_limit,
            "is_throttled": self.throttled,
            "current_cpu": psutil.cpu_percent(interval=None),
            "current_ram": psutil.virtual_memory().percent
        }

    def metrics(self) -> Dict[str, Any]:
        return {
            "throttling_events": 0 # Placeholder
        }
