import uuid
import socket
from typing import Dict, Any

class NodeIdentity:
    def __init__(self):
        self.node_id = str(uuid.uuid4())
        self.hostname = socket.gethostname()
        self.os = "unknown" # Should be detected

    def get_identity(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "hostname": self.hostname,
            "role": "CORE" # Default role
        }
