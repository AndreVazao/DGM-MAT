import time
import asyncio
from typing import Dict, Any, List
from core.provider_sync.provider_registry import provider_registry
from core.observability.logger import dgm_logger
from core.realtime.realtime_broadcast import safe_broadcast

class ProviderHealthMonitor:
    def __init__(self):
        self.check_interval = 300 # 5 minutes
        self._running = False

    async def start(self):
        self._running = True
        dgm_logger.info("ProviderHealthMonitor: Starting periodic health checks.")
        while self._running:
            await self.check_all()
            await asyncio.sleep(self.check_interval)

    def stop(self):
        self._running = False

    async def check_all(self):
        providers = provider_registry.list_providers()
        for name in providers:
            provider = provider_registry.get_provider(name)
            if provider:
                try:
                    # In real operation, we'd do a small ping request
                    health = provider.check_health()
                    dgm_logger.info(f"HealthMonitor: '{name}' status: {health['status']}")
                    provider.broadcast_health()

                    # Automatic fallback trigger logic could be here
                    if health['status'] == 'error':
                        dgm_logger.warning(f"HealthMonitor: Provider '{name}' is in error state.")
                        # Could trigger a notification or internal event
                except Exception as e:
                    dgm_logger.error(f"HealthMonitor: Failed check for '{name}': {e}")

# Singleton
health_monitor = ProviderHealthMonitor()
