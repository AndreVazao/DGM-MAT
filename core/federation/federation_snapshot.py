from datetime import datetime
from typing import List, Dict
from pydantic import BaseModel, Field
from core.federation.federation_models import EcosystemProfile

class FederationSnapshot(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    registered_ecosystems: List[EcosystemProfile]
    active_routes: List[Dict[str, str]]
    shared_knowledge_size: int
    federation_health: float
