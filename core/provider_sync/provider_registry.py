import json
from typing import Dict, List, Optional
from core.storage.storage_manager import storage_manager
from core.observability.logger import dgm_logger
from core.providers.base.provider_base import ProviderBase


class ProviderRegistry:
    """
    Governed provider registry.

    Providers are registered explicitly by trusted runtime code.
    Files dropped into core/providers are never auto-imported or executed.
    """
    def __init__(self):
        self._providers: Dict[str, ProviderBase] = {}
        self.config_file = "provider_configs.json"
        self.priority_order = [
            "chatgpt", "grok", "gemini", "deepseek", "qwen", "claude",
            "poisongpt", "z"
        ]

    def register(self, name: str, adapter: ProviderBase):
        if not name or not isinstance(adapter, ProviderBase):
            raise TypeError("Provider registration requires a name and ProviderBase instance")
        self._providers[name] = adapter
        dgm_logger.info(f"ProviderRegistry: Registered provider '{name}'")

    def get_provider(self, name: str) -> Optional[ProviderBase]:
        return self._providers.get(name)

    def list_providers(self) -> List[str]:
        registered = list(self._providers.keys())
        return sorted(
            registered,
            key=lambda x: (
                self.priority_order.index(x) if x in self.priority_order else 999,
                x,
            ),
        )

    def discover_providers(self) -> List[str]:
        """
        Discovery is observation-only.

        The canonical runtime must not import arbitrary provider source from disk.
        Promotion/registration belongs to a separately governed capability path.
        """
        return []

    def save_configs(self):
        configs = {name: provider.config for name, provider in self._providers.items()}
        storage_manager.save_data("governance", self.config_file, json.dumps(configs))
        dgm_logger.info("ProviderRegistry: Configurations persisted.")

    def load_configs(self):
        data = storage_manager.read_data("governance", self.config_file)
        if not data:
            return
        try:
            configs = json.loads(data)
            for name, config in configs.items():
                provider = self.get_provider(name)
                if provider:
                    provider.config.update(config)
                    dgm_logger.info(f"ProviderRegistry: Applied config for '{name}'")
        except Exception as exc:
            dgm_logger.error(f"ProviderRegistry: Failed to load configs: {exc}")


provider_registry = ProviderRegistry()


def initialize_default_providers():
    """
    Preserve the historical bootstrap API without auto-discovering code.
    Current canonical runtime starts with an explicitly registered set.
    """
    provider_registry.load_configs()
