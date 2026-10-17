from typing import List, Dict, Any, Optional
from core.providers.base.provider_base import ProviderBase
from core.observability.logger import dgm_logger

class GrokProvider(ProviderBase):
    def __init__(self):
        super().__init__("grok")
        self.update_capabilities(
            coding=0.85,
            reasoning=0.9,
            speed=0.9,
            context_size=131072,
            cost_profile="medium"
        )

    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        api_key = self.get_credential("api_key")
        if not api_key:
            self.health_metrics["status"] = "unauthorized"
            return "Error: xAI/Grok API key missing."

        dgm_logger.info(f"GrokProvider: Sending chat request.")
        self.record_latency(1800)
        return "Grok response placeholder"

    def check_health(self) -> Dict[str, Any]:
        api_key = self.get_credential("api_key")
        if not api_key:
            self.health_metrics["status"] = "unauthorized"
        else:
            self.health_metrics["status"] = "ok"
        return super().check_health()
