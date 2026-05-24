from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel, Field

class EcosystemStatus(str, Enum):
    PLANNED = "planned"
    RESERVED = "reserved"
    EXPERIMENTAL = "experimental"
    ACTIVE = "active"
    DEGRADED = "degraded"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"

class EcosystemRole(str, Enum):
    CORE = "core"
    INFRA = "infra"
    PRODUCT = "product"
    DATA = "data"
    AGENTS = "agents"
    EXPERIMENTAL = "experimental"
    # New roles from Strategic Architecture v1
    FINANCE = "finance"
    UI = "ui"
    PROVIDERS = "providers"
    CONNECTORS = "connectors"
    LABS = "labs"
    MEMORY = "memory"
    EXTERNAL_LABS = "external-labs"

class EcosystemNode(BaseModel):
    name: str
    role: EcosystemRole
    status: EcosystemStatus = EcosystemStatus.PLANNED
    dependencies: List[str] = Field(default_factory=list)
    health_score: float = 1.0
    last_sync: datetime = Field(default_factory=datetime.now)
    owner: str = "system"
    description: Optional[str] = None
    metadata: Dict[str, str] = Field(default_factory=dict)

class EcosystemState(BaseModel):
    nodes: Dict[str, EcosystemNode] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.now)
