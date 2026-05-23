from core.storage.storage_manager import storage_manager

# Deprecated: SESSION_PATH should be resolved via storage_manager
SESSION_PATH = storage_manager.get_path("sessions")

class SessionManager:
    def __init__(self):
        self.storage = storage_manager
        self.session_dir = self.storage.get_path("sessions")

    def get_session_path(self, session_id: str) -> str:
        return str(self.storage.get_path("sessions", f"{session_id}.json"))
