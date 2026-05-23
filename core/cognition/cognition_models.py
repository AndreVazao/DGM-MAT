from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class NodeCategory(str, Enum):
    REPOSITORY = "repository"
    AGENT = "agent"
    PROVIDER = "provider"
    NODE = "node"
    WORKFLOW = "workflow"
    MEMORY_DOMAIN = "memory_domain"
    EXECUTION_SYSTEM = "execution_system"

class EdgeType(str, Enum):
    DEPENDENCY = "dependency"
    SIMILARITY = "similarity"
    ORCHESTRATION = "orchestration"
    OWNERSHIP = "ownership"
    RUNTIME_INTERACTION = "runtime_interaction"
    HISTORICAL_RELATION = "historical_relation"

class CognitionNode(BaseModel):
    id: str
    category: NodeCategory
    metadata: Dict[str, Any] = Field(default_factory=dict)

class CognitionEdge(BaseModel):
    source: str
    target: str
    edge_type: EdgeType
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DependencyChain(BaseModel):
    chain: List[str]
    impact_score: float

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ArchitecturalRisk(BaseModel):
    risk_id: str
    description: str
    level: RiskLevel
    affected_components: List[str]
    remediation: str

class EcosystemHealthMetrics(BaseModel):
    fragmentation_score: float
    duplication_score: float
    stability_score: float
    consistency_score: float
    overall_health: float
