from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class ConversationMessage:
    """One ordered message as represented by a source export.

    The role is preserved as supplied/normalized; it is not proof that the
    message is a confirmed user decision.
    """

    message_id: str
    role: str
    content: str
    sequence: int
    timestamp: str | None = None
    source_path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class UserIntent:
    """An explicitly evidenced user intent, separate from AI suggestions."""

    intent_id: str
    statement: str
    status: Literal["current", "confirmed", "superseded", "legacy", "conflict", "unverified", "retracted"] = "unverified"
    source_conversation_id: str | None = None
    source_message_id: str | None = None
    observed_at: str | None = None
    supersedes: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    confidence: float = 0.0
    reviewed_by_user: bool = False


@dataclass
class AIProposal:
    proposal_id: str
    statement: str
    source_conversation_id: str
    source_message_id: str | None = None
    accepted: bool | None = None
    decision_id: str | None = None


@dataclass
class UserDecision:
    decision_id: str
    statement: str
    status: Literal["confirmed", "superseded", "retracted", "unverified"] = "unverified"
    source_conversation_id: str | None = None
    source_message_id: str | None = None
    decided_at: str | None = None
    supersedes: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    confirmed_by_user: bool = False


@dataclass
class ConversationRelation:
    relation_id: str
    source_conversation_id: str
    target_conversation_id: str
    relation_type: Literal["same_project", "continues", "supersedes", "conflicts_with", "duplicates", "references"]
    evidence: list[str] = field(default_factory=list)
    confidence: float = 0.0
    reviewed_by_user: bool = False


@dataclass
class ImportCoverage:
    provider: str
    status: Literal["complete", "partial", "blocked_login", "rate_limited", "failed", "needs_user"] = "partial"
    source: str | None = None
    discovered_count: int = 0
    imported_count: int = 0
    checkpoint: str | None = None
    last_error: str | None = None
    updated_at: str | None = None

    def validate(self) -> None:
        if self.discovered_count < 0 or self.imported_count < 0:
            raise ValueError("Import counts cannot be negative")
        if self.imported_count > self.discovered_count:
            raise ValueError("Imported count cannot exceed discovered count")
        if self.status == "complete" and self.discovered_count != self.imported_count:
            raise ValueError("Complete coverage requires imported_count == discovered_count")


@dataclass
class ArtifactProvenance:
    artifact_id: str
    conversation_id: str
    message_id: str | None = None
    source_provider: str | None = None
    source_url: str | None = None
    source_path: str | None = None
    extracted_at: str | None = None
    source_fingerprint: str | None = None
    verified_against_repository: bool = False


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
    messages: list[ConversationMessage] = field(default_factory=list)


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
    provenance: ArtifactProvenance | None = None


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
