from typing import List, Dict, Any
from core.providers.base.provider_base import ProviderBase
from core.observability.logger import dgm_logger

class ProviderRoutingEngine:
    def __init__(self, providers: List[ProviderBase]):
        self.providers = providers

    def route_request(self, task_type: str) -> ProviderBase:
        """Routes a request to the best available provider based on task and health."""
        # Simplified routing logic
        best_provider = None
        min_latency = float('inf')

        for provider in self.providers:
            health = provider.check_health()
            if health['status'] == 'ok' and health.get('latency', 0) < min_latency:
                min_latency = health.get('latency', 0)
                best_provider = provider

        if not best_provider:
            # Fallback to the first provider
            return self.providers[0]

        return best_provider

    def handle_failover(self, failed_provider_id: str) -> ProviderBase:
        """Handles failover when a provider fails during execution."""
        dgm_logger.warning(f"RoutingEngine: Handling failover for {failed_provider_id}")
        # Return the next best healthy provider
        for p in self.providers:
            if p.provider_id != failed_provider_id and p.check_health()['status'] == 'ok':
                return p
        return self.providers[0]
