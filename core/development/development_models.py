from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class ImplementationStatus(str, Enum):
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    VALIDATING = "validating"
    REPAIR_LOOP = "repair_loop"
    READY_FOR_MERGE = "ready_for_merge"
    FAILED = "failed"

class SpecializedAgent(BaseModel):
    agent_id: str
    role: str
    specialization_score: float
    capabilities: List[str]

class FeaturePlan(BaseModel):
    feature_id: str
    description: str
    steps: List[Dict[str, Any]]
    assigned_agents: List[str]
    estimated_impact: float
    status: ImplementationStatus = ImplementationStatus.PLANNING

class CodeChange(BaseModel):
    file_path: str
    diff: str
    explanation: str

class ValidationResult(BaseModel):
    success: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
