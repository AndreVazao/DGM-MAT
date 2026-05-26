from core.providers.base.provider_base import ProviderBase
from core.observability.logger import dgm_logger
from typing import List, Dict, Any

class GeminiProvider(ProviderBase):
    def __init__(self):
        super().__init__("gemini")

    def authenticate(self) -> bool:
        dgm_logger.info("GeminiProvider: Authenticating with Google.")
        return True

    def list_conversations(self) -> List[Dict[str, Any]]:
        return [{"id": "g1", "title": "Gemini Chat 1"}]

    def sync_conversation(self, conversation_id: str) -> bool:
        return True

    def check_health(self) -> Dict[str, Any]:
        return {"status": "ok", "latency": 150}
