from typing import List, Dict, Any, Optional
from core.providers.base.provider_base import ProviderBase
from core.observability.logger import dgm_logger

class ClaudeProvider(ProviderBase):
    def __init__(self):
        super().__init__("claude")
        self.update_capabilities(
            coding=0.92,
            reasoning=0.96,
            speed=0.75,
            context_size=200000,
            cost_profile="high"
        )

    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        api_key = self.get_credential("api_key")
        if not api_key:
            self.health_metrics["status"] = "unauthorized"
            return "Error: Anthropic/Claude API key missing."

        dgm_logger.info(f"ClaudeProvider: Sending chat request.")
        self.record_latency(3500)
        return "Claude response placeholder"

    def check_health(self) -> Dict[str, Any]:
        api_key = self.get_credential("api_key")
        if not api_key:
            self.health_metrics["status"] = "unauthorized"
        else:
            self.health_metrics["status"] = "ok"
        return super().check_health()
