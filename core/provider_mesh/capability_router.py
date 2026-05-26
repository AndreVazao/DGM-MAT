from typing import List, Dict, Any
from core.observability.logger import dgm_logger

class CapabilityRouter:
    """Routes requests based on specialized provider capabilities."""
    def __init__(self):
        pass

    def route_by_capability(self, task: str) -> str:
        dgm_logger.info(f"CapabilityRouter: Routing task based on capability requirements: {task}")
        if "code" in task:
            return "claude-3-5-sonnet"
        return "gpt-4o"
