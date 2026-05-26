from core.providers.base.provider_base import ProviderBase
from core.observability.logger import dgm_logger
from typing import List, Dict, Any

class OllamaProvider(ProviderBase):
    def __init__(self):
        super().__init__("ollama")

    def authenticate(self) -> bool:
        return True # Local Ollama usually doesn't require auth

    def list_conversations(self) -> List[Dict[str, Any]]:
        return [] # Ollama is stateless usually, or has its own API

    def sync_conversation(self, conversation_id: str) -> bool:
        return True

    def check_health(self) -> Dict[str, Any]:
        return {"status": "ok", "local": True}
