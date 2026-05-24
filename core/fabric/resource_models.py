from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime

class FabricNode(BaseModel):
    node_id: str
    hostname: str
    role: str = "worker"
    status: str = "online"
    capabilities: List[str] = []
    resource_load: float = 0.0
    last_heartbeat: datetime = Field(default_factory=datetime.now)

class Workload(BaseModel):
    workload_id: str
    owner_node: str
    target_role: Optional[str] = None
    priority: int = 1
    payload: Dict[str, Any] = {}
