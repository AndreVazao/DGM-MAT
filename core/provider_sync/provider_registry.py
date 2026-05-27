import json
import os
import importlib
import inspect
from typing import Dict, Any, List, Optional, Type
from core.storage.storage_manager import storage_manager
from core.observability.logger import dgm_logger
from core.providers.base.provider_base import ProviderBase

class ProviderRegistry:
    def __init__(self):
        self._providers: Dict[str, ProviderBase] = {}
        self.config_file = "provider_configs.json"
        self.priority_order = [
            "chatgpt", "grok", "gemini", "deepseek", "qwen", "claude",
            "poisongpt", "z"
        ]

    def register(self, name: str, adapter: ProviderBase):
        """Registers a provider instance."""
        self._providers[name] = adapter
        dgm_logger.info(f"ProviderRegistry: Registered provider '{name}'")

    def get_provider(self, name: str) -> Optional[ProviderBase]:
        return self._providers.get(name)

    def list_providers(self) -> List[str]:
        """Returns a list of registered provider names, sorted by priority."""
        registered = list(self._providers.keys())
        # Sort based on priority_order, then alphabetical for others
        return sorted(
            registered,
            key=lambda x: (self.priority_order.index(x) if x in self.priority_order else 999, x)
        )

    def discover_providers(self):
        """
        Dynamically discovers and registers providers in core/providers/.
        Scans for subdirectories containing a provider implementation.
        """
        providers_dir = os.path.join("core", "providers")
        if not os.path.exists(providers_dir):
            return

        for entry in os.scandir(providers_dir):
            if entry.is_dir() and not entry.name.startswith("__"):
                try:
                    # Look for a module matching the directory name inside it
                    # e.g., core/providers/chatgpt/chatgpt_provider.py
                    module_name = f"core.providers.{entry.name}.{entry.name}_provider"
                    module = importlib.import_module(module_name)

                    # Find any class that inherits from ProviderBase
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and
                            issubclass(obj, ProviderBase) and
                            obj is not ProviderBase):
                            instance = obj()
                            self.register(instance.name, instance)
                            break
                except (ImportError, Exception) as e:
                    # Not every directory is a provider (e.g., base, browser, models)
                    pass

    def save_configs(self):
        """Persists all provider configurations."""
        configs = {name: p.config for name, p in self._providers.items()}
        storage_manager.save_data("governance", self.config_file, json.dumps(configs))
        dgm_logger.info("ProviderRegistry: Configurations persisted.")

    def load_configs(self):
        """Applies saved configurations to registered providers."""
        data = storage_manager.read_data("governance", self.config_file)
        if data:
            try:
                configs = json.loads(data)
                for name, config in configs.items():
                    provider = self.get_provider(name)
                    if provider:
                        provider.config.update(config)
                        dgm_logger.info(f"ProviderRegistry: Applied config for '{name}'")
            except Exception as e:
                dgm_logger.error(f"ProviderRegistry: Failed to load configs: {e}")

# Singleton
provider_registry = ProviderRegistry()

def initialize_default_providers():
    """Bootstraps the registry using dynamic discovery."""
    provider_registry.discover_providers()
    provider_registry.load_configs()
