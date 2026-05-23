from datetime import datetime
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from core.cognition.cognition_models import CognitionNode, CognitionEdge, ArchitecturalRisk, EcosystemHealthMetrics

class CognitionSnapshot(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    nodes: List[CognitionNode] = Field(default_factory=list)
    edges: List[CognitionEdge] = Field(default_factory=list)
    risks: List[ArchitecturalRisk] = Field(default_factory=list)
    health: EcosystemHealthMetrics
    convergence_opportunities: List[Dict[str, Any]] = Field(default_factory=list)
