from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

class MutationStatus(Enum):
    PROPOSED = "proposed"
    SIMULATING = "simulating"
    VALIDATED = "validated"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    ROLLED_BACK = "rolled_back"

class EvolutionProposal(BaseModel):
    proposal_id: str
    target_subsystem: str
    mutation_type: str
    description: str
    impact_analysis: Dict[str, Any] = {}
    simulation_results: Optional[Dict[str, Any]] = None
    status: MutationStatus = MutationStatus.PROPOSED
    created_at: datetime = Field(default_factory=datetime.now)

class RegenerationTask(BaseModel):
    task_id: str
    target_layer: str
    reason: str
    recovery_strategy: str
    priority: int = 1
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
