import httpx
from typing import List, Dict, Any
from core.observability.logger import dgm_logger

class OllamaAdapter:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url

    def list_models(self) -> List[str]:
        try:
            response = httpx.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            dgm_logger.debug(f"Ollama: Could not connect to {self.base_url}: {e}")
        return []

    def generate(self, model: str, prompt: str, **kwargs) -> str:
        # Implementation for Ollama generation
        return "Local AI response placeholder"
