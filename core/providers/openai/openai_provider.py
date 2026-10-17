from typing import List, Dict, Any, Optional
from core.providers.base.provider_base import ProviderBase
from core.observability.logger import dgm_logger

class OpenAIProvider(ProviderBase):
    def __init__(self):
        super().__init__("openai")
        self.update_capabilities(
            coding=0.9,
            reasoning=0.95,
            speed=0.8,
            context_size=128000,
            cost_profile="high"
        )

    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        api_key = self.get_credential("api_key")
        if not api_key:
            self.health_metrics["status"] = "unauthorized"
            return "Error: OpenAI API key missing."

        # In real operation, we'd use the openai python client or httpx
        dgm_logger.info(f"OpenAIProvider: Sending chat request with {len(messages)} messages.")
        self.record_latency(2500) # Simulating 2.5s latency
        return "OpenAI response placeholder"

    def check_health(self) -> Dict[str, Any]:
        api_key = self.get_credential("api_key")
        if not api_key:
            self.health_metrics["status"] = "unauthorized"
        else:
            self.health_metrics["status"] = "ok"

        return super().check_health()
