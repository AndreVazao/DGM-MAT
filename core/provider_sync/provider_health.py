import time
from typing import Dict

class ProviderHealthMonitor:
    """
    Monitors provider availability and performance.
    """
    def __init__(self):
        self.status = {}

    def update_status(self, provider: str, available: bool, latency: float = 0):
        self.status[provider] = {
            "available": available,
            "latency": latency,
            "last_check": time.time(),
            "status": "nominal" if available else "degraded"
        }

    def get_status(self) -> Dict[str, dict]:
        return self.status

    def is_healthy(self, provider: str) -> bool:
        return self.status.get(provider, {}).get("available", False)
