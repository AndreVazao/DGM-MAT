from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from core.storage.storage_manager import storage_manager

class ProviderBase(ABC):
    def __init__(self, provider_id: str):
        self.provider_id = provider_id
        self.credentials_path = storage_manager.get_path("governance") / f"{provider_id}_creds.enc"

    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the provider."""
        pass

    @abstractmethod
    def list_conversations(self) -> List[Dict[str, Any]]:
        """List remote conversations."""
        pass

    @abstractmethod
    def sync_conversation(self, conversation_id: str) -> bool:
        """Sync a specific conversation including attachments."""
        pass

    @abstractmethod
    def check_health(self) -> Dict[str, Any]:
        """Check provider health and connection status."""
        pass

    def store_session(self, session_data: Dict[str, Any]):
        """Securely store session/cookies."""
        # In a real implementation, this would involve encryption
        storage_manager.save_data("sessions", f"{self.provider_id}_session.json", str(session_data))

    def load_session(self) -> Optional[Dict[str, Any]]:
        """Load stored session."""
        data = storage_manager.read_data("sessions", f"{self.provider_id}_session.json")
        if data:
            return eval(data) # Simplified for now, use json in production
        return None
