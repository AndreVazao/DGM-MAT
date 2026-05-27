import uuid
import socket
import os
from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class NodeIdentity:
    """
    Unique identity for a DGM-MAT node in a federation.
    Phase 42.3-LITE - Federation Preparation.
    """
    node_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    hostname: str = field(default_factory=socket.gethostname)
    role: str = "worker" # controller, worker, observer
    capabilities: Dict[str, Any] = field(default_factory=dict)
    joined_at: float = field(default_factory=lambda: 0.0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "hostname": self.hostname,
            "role": self.role,
            "capabilities": self.capabilities
        }

# Local node identity
local_node = NodeIdentity(
    node_id=os.getenv("DGM_NODE_ID", str(uuid.uuid4())),
    role=os.getenv("DGM_NODE_ROLE", "worker")
)
