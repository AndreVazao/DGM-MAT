from typing import List, Dict, Any, Optional
import time
from core.observability.logger import dgm_logger
from core.provider_mesh.consensus_engine import ConsensusEngine
from core.provider_mesh.provider_ranker import ProviderRanker
from core.provider_sync.provider_registry import provider_registry

class ProviderOrchestrator:
    """The master controller for the provider cognitive mesh."""
    def __init__(self):
        self.consensus = ConsensusEngine()
        self.ranker = ProviderRanker()

    async def chat_with_fallback(self, messages: List[Dict[str, str]], preferred_provider: Optional[str] = None, **kwargs) -> str:
        """
        Executes a chat request with automatic fallback logic.
        """
        providers_to_try = []
        if preferred_provider:
            providers_to_try.append(preferred_provider)

        # Get all registered providers sorted by priority
        all_providers = provider_registry.list_providers()
        for p in all_providers:
            if p not in providers_to_try:
                providers_to_try.append(p)

        last_error = None
        for name in providers_to_try:
            provider = provider_registry.get_provider(name)
            if not provider or not provider.is_available():
                continue

            try:
                dgm_logger.info(f"ProviderOrchestrator: Attempting chat with '{name}'")
                response = await provider.chat(messages, **kwargs)
                if response and not response.startswith("Error:"):
                    return response
                else:
                    dgm_logger.warning(f"ProviderOrchestrator: Provider '{name}' returned error/empty.")
                    last_error = response
            except Exception as e:
                dgm_logger.error(f"ProviderOrchestrator: Exception calling '{name}': {e}")
                last_error = str(e)
                # Mark as degraded if too many errors
                provider.health_metrics["error_count"] += 1
                if provider.health_metrics["error_count"] > 5:
                    provider.set_cooldown(600) # 10 min cooldown

        return f"All providers failed. Last error: {last_error}"

    async def orchestrate_reasoning(self, query: str) -> str:
        dgm_logger.info(f"ProviderOrchestrator: Orchestrating multi-provider reasoning for: {query}")
        # Phase 42.2 expansion: multiple providers then consensus
        messages = [{"role": "user", "content": query}]
        # For simplicity, we use fallback chat for now
        return await self.chat_with_fallback(messages)

# Singleton
provider_orchestrator = ProviderOrchestrator()
