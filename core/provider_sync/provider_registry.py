import json
from typing import Dict, Any, List, Optional
from core.storage.storage_manager import storage_manager
from core.observability.logger import dgm_logger

class ProviderRegistry:
    def __init__(self):
        self.providers = {}
        self.config_file = "provider_configs.json"
        self._load_configs()

    def register(self, name: str, adapter: Any):
        self.providers[name] = adapter
        dgm_logger.info(f"ProviderRegistry: Registered provider '{name}'")

    def _load_configs(self):
        """Loads provider configurations from persistent storage."""
        data = storage_manager.read_data("governance", self.config_file)
        if data:
            try:
                configs = json.loads(data)
                for name, config in configs.items():
                    # In real operation, we'd instantiate the adapter here
                    # For now, we just store the config
                    dgm_logger.info(f"ProviderRegistry: Loaded config for '{name}'")
            except Exception as e:
                dgm_logger.error(f"ProviderRegistry: Failed to load configs: {e}")

    def save_configs(self):
        """Persists all provider configurations."""
        configs = {name: getattr(p, 'config', {}) for name, p in self.providers.items()}
        storage_manager.save_data("governance", self.config_file, json.dumps(configs))
        dgm_logger.info("ProviderRegistry: Configurations persisted.")

    def get_provider(self, name: str) -> Optional[Any]:
        return self.providers.get(name)

    def list_providers(self) -> List[str]:
        return list(self.providers.keys())

# Singleton
provider_registry = ProviderRegistry()

def initialize_default_providers():
    """Bootstraps the registry with core providers."""
    from core.providers.chatgpt.chatgpt_provider import ChatGPTProvider
    from core.providers.claude.claude_provider import ClaudeProvider
    from core.providers.gemini.gemini_provider import GeminiProvider
    from core.providers.ollama.ollama_provider import OllamaProvider
    from core.providers.openrouter.openrouter_provider import OpenRouterProvider

    provider_registry.register("chatgpt", ChatGPTProvider())
    provider_registry.register("claude", ClaudeProvider())
    provider_registry.register("gemini", GeminiProvider())
    provider_registry.register("ollama", OllamaProvider())
    provider_registry.register("openrouter", OpenRouterProvider())
