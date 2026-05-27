import json
import time
from typing import Dict, Any, Optional, List
from core.realtime.realtime_broadcast import safe_broadcast
from core.security.vault import credential_vault

class ProviderBase:
    """
    Base class for all provider adapters.
    Implements mandatory contract for PHASE 42.2-LITE.
    """
    def __init__(self, name: str):
        self.name = name
        self.config = {}
        self.capabilities = {
            "coding": 0.0,
            "reasoning": 0.0,
            "speed": 0.0,
            "context_size": 0,
            "cost_profile": "medium" # 'low', 'medium', 'high'
        }
        self.health_metrics = {
            "latency": [],
            "last_check": 0,
            "status": "ok", # Default to ok for PHASE 42.2-LITE stability
            "error_count": 0,
            "quota_used": 0,
            "quota_limit": None,
            "cooldown_until": 0
        }

    def get_credential(self, cred_type: str) -> Optional[Any]:
        """Convenience method to fetch credentials for this provider."""
        return credential_vault.get_credential(self.name, cred_type)

    def set_credential(self, cred_type: str, value: Any, metadata: Optional[Dict[str, Any]] = None):
        """Convenience method to store credentials for this provider."""
        credential_vault.store_credential(self.name, cred_type, value, metadata)

    def update_capabilities(self, **kwargs):
        """Updates provider capabilities."""
        self.capabilities.update(kwargs)

    def record_latency(self, latency_ms: float):
        """Records a latency data point."""
        self.health_metrics["latency"].append(latency_ms)
        # Keep last 50 points
        if len(self.health_metrics["latency"]) > 50:
            self.health_metrics["latency"].pop(0)

    def get_avg_latency(self) -> float:
        if not self.health_metrics["latency"]:
            return 0.0
        return sum(self.health_metrics["latency"]) / len(self.health_metrics["latency"])

    def set_cooldown(self, duration_seconds: int):
        """Sets a cooldown period for the provider."""
        self.health_metrics["cooldown_until"] = time.time() + duration_seconds
        self.health_metrics["status"] = "cooldown"

    def is_available(self) -> bool:
        """Checks if the provider is currently available for use."""
        if self.health_metrics["status"] == "cooldown":
            if time.time() > self.health_metrics["cooldown_until"]:
                self.health_metrics["status"] = "ok"
                return True
            return False
        return self.health_metrics["status"] in ["ok", "degraded"]

    def broadcast_health(self):
        """Broadcasts current health status to all connected clients."""
        health = self.check_health()
        safe_broadcast({
            "type": "provider_health",
            "payload": {
                "name": self.name,
                "status": self.health_metrics["status"],
                "latency": self.get_avg_latency(),
                "quota_used": self.health_metrics["quota_used"],
                "capabilities": self.capabilities,
                "timestamp": time.time()
            }
        })

    def check_health(self) -> Dict[str, Any]:
        """
        Health check logic.
        Should be overridden by subclasses for real checks.
        """
        self.health_metrics["last_check"] = time.time()
        if self.health_metrics["status"] not in ["cooldown", "unauthorized"]:
             self.health_metrics["status"] = "ok"

        return {
            "status": self.health_metrics["status"],
            "latency": self.get_avg_latency()
        }

    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Mandatory chat interface."""
        raise NotImplementedError("Providers must implement chat()")

    def parse_session_data(self, data: str) -> Optional[Dict[str, Any]]:
        if not data:
            return None
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return None
