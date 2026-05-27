from typing import Dict, Any, List, Optional
from core.observability.logger import dgm_logger
from core.provider_sync.provider_registry import provider_registry

class ProviderRanker:
    """Ranks providers based on capabilities, cost, and health."""
    def __init__(self):
        self.weights = {
            "coding": 1.0,
            "reasoning": 1.0,
            "speed": 0.5,
            "cost": -0.5 # Negative weight for high cost
        }

    def rank_for_mission(self, requirement: str, preferred: Optional[str] = None) -> List[str]:
        """
        Ranks registered providers based on mission requirements.
        Requirements: 'coding', 'reasoning', 'speed', 'cost'.
        """
        providers = provider_registry.list_providers()
        scores = {}

        for name in providers:
            provider = provider_registry.get_provider(name)
            if not provider or not provider.is_available():
                continue

            # Base score from capabilities
            base_score = provider.capabilities.get(requirement, 0.5)

            # Adjust for health/latency
            latency = provider.get_avg_latency()
            health_penalty = 1.0
            if provider.health_metrics["status"] == "degraded":
                health_penalty = 0.5

            # Latency penalty: normalize 0-5s to 1.0-0.5
            latency_penalty = max(0.5, 1.0 - (latency / 10000))

            final_score = base_score * health_penalty * latency_penalty

            # Bonus for preferred
            if name == preferred:
                final_score += 0.5

            scores[name] = final_score

        return sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

# Singleton
provider_ranker = ProviderRanker()
