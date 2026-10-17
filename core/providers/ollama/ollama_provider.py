from typing import List, Dict, Any, Optional
from core.providers.base.provider_base import ProviderBase
from core.observability.logger import dgm_logger

class OllamaProvider(ProviderBase):
    def __init__(self):
        super().__init__("ollama")
        self.update_capabilities(
            coding=0.75,
            reasoning=0.8,
            speed=0.9,
            context_size=32000,
            cost_profile="low"
        )
        self.config["base_url"] = "http://localhost:11434"

    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        dgm_logger.info(f"OllamaProvider: Sending request to local instance.")
        self.record_latency(500)
        return "Ollama response placeholder"

    def check_health(self) -> Dict[str, Any]:
        # In real operation, we'd check if Ollama is running locally
        self.health_metrics["status"] = "ok"
        return super().check_health()
