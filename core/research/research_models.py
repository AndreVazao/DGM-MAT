from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class ExperimentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

class ExperimentType(str, Enum):
    PROVIDER_BENCHMARK = "provider_benchmark"
    ARCHITECTURE_TRIAL = "architecture_trial"
    RUNTIME_TEST = "runtime_test"
    PROTOTYPE = "prototype"

class Experiment(BaseModel):
    id: str
    name: str
    type: ExperimentType
    status: ExperimentStatus
    parameters: Dict[str, Any] = Field(default_factory=dict)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    results: Dict[str, Any] = Field(default_factory=dict)
    isolation_id: str
