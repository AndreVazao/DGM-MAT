from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class GovernanceViolation(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    violation_type: str
    severity: str
    trace_id: Optional[str] = None
    description: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ResourceSnapshot(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    cpu_percent: float
    memory_percent: float
    event_queue_size: int
    active_websockets: int
    active_browsers: int
    active_worktrees: int

class GovernanceState(BaseModel):
    is_degraded: bool = False
    emergency_slowdown: bool = False
    throttling_active: bool = False
    active_storms: List[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.now)
