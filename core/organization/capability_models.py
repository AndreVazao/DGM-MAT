"""Capability acquisition, skill provenance and recruitment domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CapabilityStatus(str, Enum):
    REQUESTED = "REQUESTED"
    DISCOVERED = "DISCOVERED"
    ASSESSED = "ASSESSED"
    SANDBOXED = "SANDBOXED"
    ADAPTED = "ADAPTED"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"
    PROMOTED = "PROMOTED"


class RecruitmentStatus(str, Enum):
    PROPOSED = "PROPOSED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    APPROVED = "APPROVED"
    BUILDING = "BUILDING"
    VALIDATING = "VALIDATING"
    HIRED = "HIRED"
    FAILED = "FAILED"
    RETIRED = "RETIRED"


@dataclass(slots=True)
class CapabilityRequest:
    request_id: str
    capability: str
    reason: str
    mission_id: str
    requested_by: str
    required_skills: list[str] = field(default_factory=list)
    preferred_sources: list[str] = field(default_factory=list)
    risk_level: str = "normal"
    status: CapabilityStatus = CapabilityStatus.REQUESTED
    created_at: datetime = field(default_factory=utc_now)


@dataclass(slots=True)
class CapabilitySource:
    source_id: str
    name: str
    source_type: str
    locator: str
    trust: float = 0.5
    license: str | None = None
    capabilities: list[str] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class CapabilityCandidate:
    candidate_id: str
    request_id: str
    source: CapabilitySource
    matched_skills: list[str] = field(default_factory=list)
    fit_score: float = 0.0
    safety_score: float = 0.0
    adaptation_cost: float = 1.0
    provenance_required: bool = True
    assessment_notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RecruitmentOrder:
    order_id: str = field(default_factory=lambda: f"hire:{uuid4().hex}")
    request_id: str = ""
    candidate_id: str = ""
    role: str = ""
    department_id: str = ""
    worker_id: str | None = None
    status: RecruitmentStatus = RecruitmentStatus.PROPOSED
    approval_required: bool = False
    approval_reason: str | None = None
    source_snapshot: str | None = None
    adapted_module: str | None = None
    validation_report: str | None = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
