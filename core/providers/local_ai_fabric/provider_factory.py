from typing import Dict, Any, Optional
from core.observability.logger import dgm_logger
from .ollama_adapter import OllamaAdapter
from .open_webui_adapter import OpenWebUIAdapter

class LocalAIFabric:
    """
    Unified access layer for local AI providers.
    """
    def __init__(self):
        self.providers = {
            "ollama": OllamaAdapter(),
            "open_webui": OpenWebUIAdapter()
        }

    def get_provider(self, name: str):
        return self.providers.get(name)

    def discover_local_models(self) -> Dict[str, Any]:
        """Scans all registered local providers for available models."""
        available = {}
        for name, provider in self.providers.items():
            try:
                models = provider.list_models()
                available[name] = models
            except Exception as e:
                dgm_logger.warning(f"LocalAIFabric: Failed to list models for {name}: {e}")
        return available
