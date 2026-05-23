from typing import Callable, Any
from core.observability.logger import dgm_logger

class IsolationEngine:
    def execute_isolated(self, task_name: str, task_fn: Callable[..., Any], *args, **kwargs) -> Any:
        try:
            return task_fn(*args, **kwargs)
        except Exception as exc:
            dgm_logger.error(f"Isolation Engine: Task '{task_name}' failed but was isolated. Error: {exc}")
            return None
