from datetime import datetime
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from core.recovery.recovery_models import HealthStatus, RecoveryAction

class RecoverySnapshot(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    health: Dict[str, HealthStatus]
    active_recovery_actions: List[RecoveryAction]
    crash_history: List[Dict[str, Any]]
    runtime_state_dump: Dict[str, Any]
