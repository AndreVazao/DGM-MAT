from typing import List, Dict, Any, Optional
from core.providers.base.provider_base import ProviderBase
from core.observability.logger import dgm_logger

class QwenProvider(ProviderBase):
    def __init__(self):
        super().__init__("qwen")
        self.update_capabilities(
            coding=0.88,
            reasoning=0.88,
            speed=0.92,
            context_size=32000,
            cost_profile="low"
        )

    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        api_key = self.get_credential("api_key")
        if not api_key:
            self.health_metrics["status"] = "unauthorized"
            return "Error: Qwen API key missing."

        dgm_logger.info(f"QwenProvider: Sending chat request.")
        self.record_latency(1500)
        return "Qwen response placeholder"

    def check_health(self) -> Dict[str, Any]:
        api_key = self.get_credential("api_key")
        if not api_key:
            self.health_metrics["status"] = "unauthorized"
        else:
            self.health_metrics["status"] = "ok"
        return super().check_health()
