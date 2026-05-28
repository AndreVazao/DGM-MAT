from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class MissionStatus(Enum):
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    APPROVAL_PENDING = "APPROVAL_PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

@dataclass
class SubTask:
    subtask_id: str
    title: str
    description: str
    status: str = "pending"
    assigned_agent: Optional[str] = None
    task_id: Optional[str] = None # Link to AutonomousTask if dispatched
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

@dataclass
class Mission:
    mission_id: str
    goal: str
    description: str
    status: MissionStatus = MissionStatus.CREATED
    subtasks: List[SubTask] = field(default_factory=list)
    assigned_agents: List[str] = field(default_factory=list)
    artifacts: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    execution_timeline: List[Dict[str, Any]] = field(default_factory=list)
