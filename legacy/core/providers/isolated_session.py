import uuid
import datetime
from typing import Dict, Any, List

class IsolatedSession:
    def __init__(self, provider_name: str):
        self.session_id = str(uuid.uuid4())
        self.provider = provider_name
        self.start_time = datetime.datetime.utcnow().isoformat()
        self.events: List[Dict[str, Any]] = []
        self.status = "active"

    def log_interaction(self, input_data: str, output_data: str):
        event = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "input": input_data,
            "output": output_data,
            "trace_id": str(uuid.uuid4())
        }
        self.events.append(event)
        return event

    def close(self):
        self.status = "closed"
        self.end_time = datetime.datetime.utcnow().isoformat()

class ProviderManager:
    def __init__(self):
        self.active_sessions: Dict[str, IsolatedSession] = {}

    def create_session(self, provider_name: str) -> str:
        session = IsolatedSession(provider_name)
        self.active_sessions[session.session_id] = session
        return session.session_id

    def get_session(self, session_id: str) -> IsolatedSession:
        return self.active_sessions.get(session_id)

    def close_session(self, session_id: str):
        if session_id in self.active_sessions:
            self.active_sessions[session_id].close()
            # In a real system, we would persist the session logs before removal
            del self.active_sessions[session_id]
