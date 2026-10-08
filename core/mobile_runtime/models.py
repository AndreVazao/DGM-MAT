# Path: C:\ProgramasGodMode\DGM-MAT\core\mobile_runtime\models.py
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ConversationMessage:
    id: str
    role: str
    content: str
    created_at: str = field(default_factory=utc_now)
    state: str = "ready"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationThread:
    id: str
    title: str
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    project: str | None = None
    repository: str | None = None
    status: str = "active"
    messages: list[ConversationMessage] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class IntentResult:
    intent: str
    summary: str
    confidence: float
    project_hint: str | None = None
    repository_hint: str | None = None
    action: str | None = None
    requires_approval: bool = False
    execution_candidate: bool = False
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
