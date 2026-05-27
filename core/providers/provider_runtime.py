import time
from core.provider_sync.provider_registry import provider_registry, initialize_default_providers
from core.observability.logger import dgm_logger

class ProviderRuntime:
    def __init__(self):
        initialize_default_providers()

    def run(self):
        dgm_logger.info("ProviderRuntime: Starting provider health checks and sync...")
        providers = provider_registry.list_providers()

        for name in providers:
            provider = provider_registry.get_provider(name)
            if provider:
                try:
                    dgm_logger.info(f"ProviderRuntime: Checking health for '{name}'")
                    provider.broadcast_health()
                except Exception as e:
                    dgm_logger.error(f"ProviderRuntime: Failed health check for '{name}': {e}")

        dgm_logger.info("ProviderRuntime: Provider sweep complete.")

if __name__ == "__main__":
    ProviderRuntime().run()
