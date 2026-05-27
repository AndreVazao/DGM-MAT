from typing import List, Dict, Any, Optional
from core.providers.base.provider_base import ProviderBase
from core.observability.logger import dgm_logger

class PoisonGPTProvider(ProviderBase):
    def __init__(self):
        super().__init__("poisongpt")
        self.update_capabilities(
            coding=0.5,
            reasoning=0.5,
            speed=0.9,
            context_size=8192,
            cost_profile="low"
        )

    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        dgm_logger.warning("PoisonGPTProvider: Experimental provider called.")
        self.record_latency(100)
        return "PoisonGPT experimental response"

    def check_health(self) -> Dict[str, Any]:
        self.health_metrics["status"] = "ok"
        return super().check_health()
