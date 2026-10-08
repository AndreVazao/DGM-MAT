import json
import os
import socket
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

IDENTITY_FILE = Path("C:/ProgramasGodMode/DGM-MAT/config/node_identity.json")


def _load_or_create_id() -> str:
    configured = os.getenv("DGM_NODE_ID")
    if configured:
        return configured
    try:
        if IDENTITY_FILE.exists():
            data = json.loads(IDENTITY_FILE.read_text(encoding="utf-8"))
            if data.get("node_id"):
                return str(data["node_id"])
    except Exception:
        pass
    node_id = str(uuid.uuid4())
    try:
        IDENTITY_FILE.parent.mkdir(parents=True, exist_ok=True)
        IDENTITY_FILE.write_text(json.dumps({"node_id": node_id}, indent=2), encoding="utf-8")
    except Exception:
        pass
    return node_id


@dataclass
class NodeIdentity:
    node_id: str = field(default_factory=_load_or_create_id)
    hostname: str = field(default_factory=socket.gethostname)
    role: str = "worker"
    capabilities: Dict[str, Any] = field(default_factory=dict)
    joined_at: float = field(default_factory=lambda: 0.0)

    def to_dict(self) -> Dict[str, Any]:
        return {"node_id": self.node_id, "hostname": self.hostname, "role": self.role, "capabilities": self.capabilities}


local_node = NodeIdentity(role=os.getenv("DGM_NODE_ROLE", "worker"))
