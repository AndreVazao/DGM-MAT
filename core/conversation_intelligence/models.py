from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class ConversationRecord:
    conversation_id: str
    provider: str
    title: str
    content: str
    source: str = "import"
    url: str | None = None
    detected_projects: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class CodeArtifact:
    artifact_id: str
    conversation_id: str
    provider: str
    language: str
    code: str
    file_path: str | None = None
    source_marker: str | None = None
    fingerprint: str = ""
    syntax_ok: bool | None = None
    context_score: float = 0.0
    findings: list[str] = field(default_factory=list)

@dataclass
class AuditFinding:
    severity: str
    category: str
    message: str
    conversation_id: str | None = None
    artifact_id: str | None = None
    file_path: str | None = None

@dataclass
class ConversationAudit:
    conversation: ConversationRecord
    artifacts: list[CodeArtifact] = field(default_factory=list)
    findings: list[AuditFinding] = field(default_factory=list)
    suggested_project: str | None = None
    suggested_title: str | None = None