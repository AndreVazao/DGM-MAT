from datetime import datetime
from typing import List, Dict
from pydantic import BaseModel, Field
from core.research.research_models import Experiment

class ExperimentSnapshot(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    active_experiments: List[Experiment]
    sandbox_status: Dict[str, str]
    resource_usage: Dict[str, float]
