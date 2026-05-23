from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class KnowledgeCategory(str, Enum):
    ARCHITECTURE = "architecture"
    RUNTIME = "runtime"
    RECOVERY = "recovery"
    PROVIDER = "provider"
    REPOSITORY = "repository"
    COGNITION = "cognition"

class RelationshipType(str, Enum):
    DEPENDS_ON = "depends_on"
    RELATED_TO = "related_to"
    CAUSED_BY = "caused_by"
    EVOLVED_FROM = "evolved_from"
    Specializes = "specializes"

class KnowledgeNode(BaseModel):
    id: str
    category: KnowledgeCategory
    name: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)

class KnowledgeEdge(BaseModel):
    source: str
    target: str
    relation: RelationshipType
    metadata: Dict[str, Any] = Field(default_factory=dict)
    weight: float = 1.0

class SemanticSnapshot(BaseModel):
    id: str = Field(default_factory=lambda: str(datetime.now().timestamp()))
    nodes: List[KnowledgeNode]
    edges: List[KnowledgeEdge]
    timestamp: datetime = Field(default_factory=datetime.now)
