from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class CrashSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class CrashType(str, Enum):
    PROVIDER_CRASH = "provider_crash"
    RUNTIME_CRASH = "runtime_crash"
    WEBSOCKET_DISCONNECT = "websocket_disconnect"
    MEMORY_CORRUPTION = "memory_corruption"
    NODE_LOSS = "node_loss"
    DEADLOCK = "deadlock"
    EXECUTION_TIMEOUT = "execution_timeout"
    EVENT_BUS_FAILURE = "event_bus_failure"

class RecoveryStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    DEGRADED = "degraded"

class HealthStatus(BaseModel):
    is_healthy: bool
    last_check: datetime = Field(default_factory=datetime.now)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)

class RecoveryAction(BaseModel):
    id: str
    action_type: str
    target: str
    status: RecoveryStatus = RecoveryStatus.PENDING
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
