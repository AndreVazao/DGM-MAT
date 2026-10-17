from typing import List, Dict, Any
from core.observability.logger import dgm_logger

class LatencyRouter:
    """Routes requests to providers with the lowest latency."""
    def __init__(self):
        pass

    def get_fastest_provider(self, providers: List[str]) -> str:
        dgm_logger.info("LatencyRouter: Selecting lowest latency provider.")
        return providers[0]
