from typing import Dict, Any
from core.observability.logger import dgm_logger
from core.model_router.model_registry import ModelRegistry

class RoutingEngine:
    def __init__(self):
        self.registry = ModelRegistry()

    def route_task(self, task_complexity: int) -> str:
        dgm_logger.info(f"RoutingEngine: Routing task with complexity {task_complexity}")
        # Simplistic routing: choose the smallest model that fits the complexity
        suitable_models = [
            (m, info) for m, info in self.registry.models.items()
            if info["complexity_limit"] >= task_complexity and info["type"] == "local"
        ]

        if not suitable_models:
            dgm_logger.warning("RoutingEngine: No suitable local model found. Falling back to remote.")
            return "gpt-4o-mini"

        # Return the one with the lowest limit that still satisfies (efficiency)
        suitable_models.sort(key=lambda x: x[1]["complexity_limit"])
        return suitable_models[0][0]
