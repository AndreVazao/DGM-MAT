from datetime import datetime
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from core.development.development_models import FeaturePlan, SpecializedAgent

class DevelopmentSnapshot(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    active_plans: List[FeaturePlan]
    agent_pool: List[SpecializedAgent]
    execution_stats: Dict[str, Any]
