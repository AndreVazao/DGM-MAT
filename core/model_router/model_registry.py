from typing import Dict, List, Any
from core.observability.logger import dgm_logger

class ModelRegistry:
    def __init__(self):
        self.models = {
            "llama3": {"provider": "ollama", "type": "local", "complexity_limit": 80},
            "phi3": {"provider": "ollama", "type": "local", "complexity_limit": 40},
            "gpt-4o-mini": {"provider": "openai", "type": "remote", "complexity_limit": 100}
        }

    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        return self.models.get(model_id, {})

    def list_available_models(self) -> List[str]:
        return list(self.models.keys())
