import json
import time
from typing import Dict, Any, Optional
from core.realtime.realtime_broadcast import safe_broadcast

class ProviderBase:
    """Base class for all provider adapters."""
    def __init__(self, name: str):
        self.name = name
        self.config = {}

    def parse_session_data(self, data: str) -> Optional[Dict[str, Any]]:
        if not data:
            return None
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return None

    def broadcast_health(self):
        """Broadcasts current health status to all connected clients."""
        health = self.check_health()
        safe_broadcast({
            "type": "provider_health",
            "payload": {
                "name": self.name,
                "status": health.get("status", "unknown"),
                "latency": health.get("latency", 0),
                "timestamp": time.time()
            }
        })

    def check_health(self) -> Dict[str, Any]:
        """Placeholder for health check logic."""
        return {"status": "ok", "latency": 0}
