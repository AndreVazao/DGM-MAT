"""Canonical domain models for the DGM-MAT digital organization."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AgentStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    BUSY = "BUSY"
    BLOCKED = "BLOCKED"
    OFFLINE = "OFFLINE"
    SUSPENDED = "SUSPENDED"


class TaskStatus(str, Enum):
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    ASSIGNED = "ASSIGNED"
    RUNNING = "RUNNING"
    BLOCKED = "BLOCKED"
    REVIEW = "REVIEW"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class MessagePriority(str, Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(slots=True)
class Department:
    department_id: str
    name: str
    mission: str
    capabilities: list[str] = field(default_factory=list)
    allowed_scopes: list[str] = field(default_factory=list)
    active: bool = True


@dataclass(slots=True)
class AgentProfile:
    agent_id: str
    name: str
    department_id: str
    role: str
    skills: list[str] = field(default_factory=list)
    responsibilities: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    status: AgentStatus = AgentStatus.AVAILABLE
    version: str = "1.0.0"
    supervisor_id: str | None = None
    memory_scope: str = "agent"
    performance: dict[str, float] = field(default_factory=dict)
    lessons: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)


@dataclass(slots=True)
class Evidence:
    evidence_id: str = field(default_factory=lambda: f"ev:{uuid4().hex}")
    kind: str = "observation"
    source: str = ""
    locator: str | None = None
    summary: str = ""
    confidence: float = 1.0
    captured_at: datetime = field(default_factory=utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Task:
    task_id: str
    title: str
    mission_id: str
    description: str
    owner_department: str | None = None
    assigned_agent: str | None = None
    status: TaskStatus = TaskStatus.CREATED
    priority: int = 50
    dependencies: list[str] = field(default_factory=list)
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    approval_required: bool = False
    approval_reason: str | None = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)


@dataclass(slots=True)
class Message:
    sender_id: str
    recipient_id: str
    subject: str
    body: str
    message_id: str = field(default_factory=lambda: f"msg:{uuid4().hex}")
    task_id: str | None = None
    mission_id: str | None = None
    priority: MessagePriority = MessagePriority.NORMAL
    evidence: list[Evidence] = field(default_factory=list)
    requires_response: bool = False
    correlation_id: str | None = None
    created_at: datetime = field(default_factory=utc_now)
    read_at: datetime | None = None


@dataclass(slots=True)
class EvolutionProposal:
    proposal_id: str
    agent_id: str
    reason: str
    observed_problem: str
    proposed_change: str
    expected_benefit: str
    evidence: list[Evidence] = field(default_factory=list)
    status: str = "PROPOSED"
    current_version: str = "1.0.0"
    proposed_version: str | None = None
    evaluation: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
