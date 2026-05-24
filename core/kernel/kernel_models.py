from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

class KernelStatus(Enum):
    INITIALIZING = "initializing"
    RUNNING = "running"
    DEGRADED = "degraded"
    RECOVERING = "recovering"
    STORM_PROTECTION = "storm_protection"
    SHUTTING_DOWN = "shutting_down"

class ExecutionContext(BaseModel):
    execution_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    runtime_state: Dict[str, Any] = {}
    governance_state: Dict[str, Any] = {}
    semantic_context: Dict[str, Any] = {}
    strategic_priorities: List[str] = []
    resource_pressure: float = 0.0
    provider_health: Dict[str, float] = {}
    federation_state: Dict[str, Any] = {}
    memory_state: Dict[str, Any] = {}

class KernelState(BaseModel):
    status: KernelStatus = KernelStatus.INITIALIZING
    active_contexts: Dict[str, ExecutionContext] = {}
    subsystem_health: Dict[str, str] = {}
    last_snapshot_at: Optional[datetime] = None
    cognition_load: float = 0.0
    orchestration_pressure: float = 0.0

class CognitionRoute(BaseModel):
    source_event: str
    target_specialization: str
    priority: int
    context_requirements: List[str] = []
    estimated_load: float = 0.1
