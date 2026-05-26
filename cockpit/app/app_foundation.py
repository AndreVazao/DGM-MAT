from typing import Dict, Any, List
from core.storage.storage_manager import storage_manager
from core.observability.logger import dgm_logger
import json

class CockpitState:
    """Manages the persistent state of the Cockpit interface."""
    def __init__(self):
        self.sessions_file = "cockpit_sessions.json"
        self.active_chats: List[Dict[str, Any]] = []

    def save_chat(self, chat_id: str, messages: List[Dict[str, str]]):
        chat_data = {"chat_id": chat_id, "messages": messages}
        # Simplified: find and update or append
        self.active_chats = [c for c in self.active_chats if c['chat_id'] != chat_id]
        self.active_chats.append(chat_data)
        self.persist()

    def persist(self):
        storage_manager.save_data("sessions", self.sessions_file, json.dumps(self.active_chats))

    def load_state(self):
        data = storage_manager.read_data("sessions", self.sessions_file)
        if data:
            self.active_chats = json.loads(data)
            dgm_logger.info(f"CockpitState: Loaded {len(self.active_chats)} chat sessions.")
