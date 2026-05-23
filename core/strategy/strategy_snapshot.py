from datetime import datetime
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from core.strategy.roadmap_models import StrategicObjective, Milestone, TechnicalDebt

class StrategySnapshot(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    active_objectives: List[StrategicObjective]
    pending_milestones: List[Milestone]
    detected_debt: List[TechnicalDebt]
    sustainability_index: float
    ecosystem_health: float
    risk_forecast: Dict[str, Any]
