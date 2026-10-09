import json
import time
from typing import Dict, Any, Optional, List
from core.realtime.realtime_broadcast import safe_broadcast
from core.security.vault import credential_vault

class ProviderBase:
    """
    Base class for all provider adapters.
    Implements mandatory provider contract.
    """
    def __init__(self, name: str):
        self.name = name
        self.config = {}
        self.capabilities = {
            "coding": 0.0,
            "reasoning": 0.0,
            "speed": 0.0,
            "context_size": 0,
            "cost_profile": "medium"
        }
        self.health_metrics = {
            "latency": [],
            # Timestamp of an actual health observation; base implementation leaves it unchanged.
            "last_check": 0,
            # Timestamp of the latest attempt to check health, including unverified base calls.
            "last_check_attempt": 0,
            "status": "unknown",
            "error_count": 0,
            "quota_used": 0,
            "quota_limit": None,
            "cooldown_until": 0
        }

    def get_credential(self, cred_type: str) -> Optional[Any]:
        return credential_vault.get_credential(self.name, cred_type)

    def set_credential(self, cred_type: str, value: Any, metadata: Optional[Dict[str, Any]] = None):
        credential_vault.store_credential(self.name, cred_type, value, metadata)

    def update_capabilities(self, **kwargs):
        self.capabilities.update(kwargs)

    def record_latency(self, latency_ms: float):
        self.health_metrics["latency"].append(latency_ms)
        if len(self.health_metrics["latency"]) > 50:
            self.health_metrics["latency"].pop(0)

    def get_avg_latency(self) -> float:
        if not self.health_metrics["latency"]:
            return 0.0
        return sum(self.health_metrics["latency"]) / len(self.health_metrics["latency"])

    def set_cooldown(self, duration_seconds: int):
        self.health_metrics["cooldown_until"] = time.time() + duration_seconds
        self.health_metrics["status"] = "cooldown"

    def is_available(self) -> bool:
        status = self.health_metrics["status"]
        if status == "cooldown":
            if time.time() > self.health_metrics["cooldown_until"]:
                self.health_metrics["status"] = "unknown"
            return False
        return status in ["ok", "degraded"]

    def broadcast_health(self):
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
        Base implementation cannot prove remote health.

        last_check_attempt records that this method was invoked.
        last_check is reserved for a concrete, observed health result.
        Concrete adapters must override this method to establish health.
        """
        now = time.time()
        self.health_metrics["last_check_attempt"] = now

        if self.health_metrics["status"] == "cooldown":
            if now > self.health_metrics["cooldown_until"]:
                self.health_metrics["status"] = "unknown"
        else:
            # Never trust a prior/manual status without a concrete health observation.
            self.health_metrics["status"] = "unknown"

        return {
            "status": self.health_metrics["status"],
            "latency": self.get_avg_latency()
        }

    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        raise NotImplementedError("Providers must implement chat()")

    def parse_session_data(self, data: str) -> Optional[Dict[str, Any]]:
        if not data:
            return None
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return None
