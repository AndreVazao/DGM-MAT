from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class PlanningHorizon(str, Enum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"

class PriorityCategory(str, Enum):
    CRITICAL = "critical"
    STRATEGIC = "strategic"
    MAINTENANCE = "maintenance"
    OPTIMIZATION = "optimization"
    EXPERIMENTAL = "experimental"

class StrategicObjective(BaseModel):
    id: str
    title: str
    description: str
    horizon: PlanningHorizon
    priority: PriorityCategory
    status: str = "pending"
    progress: float = 0.0

class Milestone(BaseModel):
    id: str
    objective_id: str
    title: str
    due_date: datetime
    completed: bool = False
    dependencies: List[str] = Field(default_factory=list)

class TechnicalDebt(BaseModel):
    id: str
    component: str
    debt_score: float
    urgency: str
    risk_projection: str
    remediation_plan: str

class Roadmap(BaseModel):
    id: str
    name: str
    objectives: List[StrategicObjective]
    milestones: List[Milestone]
    created_at: datetime = Field(default_factory=datetime.now)
