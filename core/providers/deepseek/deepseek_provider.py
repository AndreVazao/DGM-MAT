from typing import List, Dict, Any, Optional
from core.providers.base.provider_base import ProviderBase
from core.observability.logger import dgm_logger

class DeepSeekProvider(ProviderBase):
    def __init__(self):
        super().__init__("deepseek")
        self.update_capabilities(
            coding=0.92,
            reasoning=0.9,
            speed=0.85,
            context_size=64000,
            cost_profile="low"
        )

    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        api_key = self.get_credential("api_key")
        if not api_key:
            self.health_metrics["status"] = "unauthorized"
            return "Error: DeepSeek API key missing."

        dgm_logger.info(f"DeepSeekProvider: Sending chat request.")
        self.record_latency(2000)
        return "DeepSeek response placeholder"

    def check_health(self) -> Dict[str, Any]:
        api_key = self.get_credential("api_key")
        if not api_key:
            self.health_metrics["status"] = "unauthorized"
        else:
            self.health_metrics["status"] = "ok"
        return super().check_health()
