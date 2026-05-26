from core.providers.base.provider_base import ProviderBase
from core.observability.logger import dgm_logger
from typing import List, Dict, Any

class OpenWebUIProvider(ProviderBase):
    def __init__(self):
        super().__init__("openwebui")

    def authenticate(self) -> bool:
        return True

    def list_conversations(self) -> List[Dict[str, Any]]:
        return [{"id": "ow1", "title": "OpenWebUI Chat"}]

    def sync_conversation(self, conversation_id: str) -> bool:
        return True

    def check_health(self) -> Dict[str, Any]:
        return {"status": "ok"}
