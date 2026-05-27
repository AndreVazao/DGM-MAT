from typing import List, Dict, Any, Optional
from core.providers.base.provider_base import ProviderBase
from core.observability.logger import dgm_logger

class CustomProvider(ProviderBase):
    def __init__(self):
        super().__init__("custom")
        self.update_capabilities(
            coding=0.0,
            reasoning=0.0,
            speed=0.0,
            context_size=0,
            cost_profile="medium"
        )

    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        endpoint = self.config.get("endpoint")
        if not endpoint:
            return "Error: Custom provider endpoint not configured."

        dgm_logger.info(f"CustomProvider: Calling {endpoint}")
        self.record_latency(1000)
        return "Custom provider response"

    def check_health(self) -> Dict[str, Any]:
        if "endpoint" in self.config:
            self.health_metrics["status"] = "ok"
        else:
            self.health_metrics["status"] = "degraded"
        return super().check_health()
