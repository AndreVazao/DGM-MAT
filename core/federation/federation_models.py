from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class TrustLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERIFIED = "verified"

class EcosystemStatus(str, Enum):
    PLANNED = "planned"
    RESERVED = "reserved"
    EXPERIMENTAL = "experimental"
    ACTIVE = "active"
    DEGRADED = "degraded"
    ARCHIVED = "archived"

class EcosystemProfile(BaseModel):
    id: str
    name: str
    specialization: List[str]
    trust_score: float = 0.0
    trust_level: TrustLevel = TrustLevel.LOW
    status: EcosystemStatus = EcosystemStatus.RESERVED
    last_seen: datetime = Field(default_factory=datetime.now)

class FederationMessage(BaseModel):
    id: str
    source_ecosystem: str
    target_ecosystem: str
    payload: Dict[str, Any]
    signature: str
    timestamp: datetime = Field(default_factory=datetime.now)

class FederationPolicy(BaseModel):
    ecosystem_id: str
    permissions: List[str]
    resource_limits: Dict[str, float]
