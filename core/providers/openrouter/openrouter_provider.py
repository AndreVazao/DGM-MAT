from typing import List, Dict, Any, Optional
from core.providers.base.provider_base import ProviderBase
from core.observability.logger import dgm_logger

class OpenRouterProvider(ProviderBase):
    def __init__(self):
        super().__init__("openrouter")
        self.update_capabilities(
            coding=0.9,
            reasoning=0.9,
            speed=0.8,
            context_size=128000,
            cost_profile="medium"
        )

    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        api_key = self.get_credential("api_key")
        if not api_key:
            self.health_metrics["status"] = "unauthorized"
            return "Error: OpenRouter API key missing."

        dgm_logger.info(f"OpenRouterProvider: Sending chat request.")
        self.record_latency(2800)
        return "OpenRouter response placeholder"

    def check_health(self) -> Dict[str, Any]:
        api_key = self.get_credential("api_key")
        if not api_key:
            self.health_metrics["status"] = "unauthorized"
        else:
            self.health_metrics["status"] = "ok"
        return super().check_health()
