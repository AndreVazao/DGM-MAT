from typing import List, Dict, Any, Optional
from core.providers.base.provider_base import ProviderBase
from core.observability.logger import dgm_logger
from core.providers.performance.provider_capability_matrix import capability_matrix

class ProviderRoutingEngine:
    """
    Intelligent Provider Routing Engine - Phase 42.3-LITE.
    Routes tasks based on capability, health, and latency.
    """
    def __init__(self, providers: List[ProviderBase]):
        self.providers = {p.name: p for p in providers}

    def route_request(self, task_type: str, required_capability: Optional[str] = None) -> ProviderBase:
        """
        Routes a request using capability matrix and health checks.
        """
        cap = required_capability or task_type
        fallback_chain = capability_matrix.get_fallback_chain(cap)

        for provider_name in fallback_chain:
            provider = self.providers.get(provider_name)
            if provider and provider.is_available():
                dgm_logger.info(f"RoutingEngine: Routed {task_type} to {provider_name}")
                return provider

        # Ultimate fallback
        dgm_logger.warning(f"RoutingEngine: No ideal provider for {cap}. Using first available.")
        for p in self.providers.values():
            if p.is_available():
                return p

        raise RuntimeError("No providers available for routing.")

    def handle_failover(self, failed_provider_name: str, task_type: str) -> ProviderBase:
        """Handles failover by picking the next best provider in the chain."""
        dgm_logger.warning(f"RoutingEngine: Handling failover for {failed_provider_name} ({task_type})")

        fallback_chain = capability_matrix.get_fallback_chain(task_type)
        found_current = False

        for provider_name in fallback_chain:
            if provider_name == failed_provider_name:
                found_current = True
                continue

            if found_current:
                provider = self.providers.get(provider_name)
                if provider and provider.is_available():
                    dgm_logger.info(f"RoutingEngine: Failover routed to {provider_name}")
                    return provider

        return self.route_request(task_type)
