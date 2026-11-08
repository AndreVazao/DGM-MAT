"""Evidence-bounded, read-only design-review packet contracts.

This module prepares isolated reviewer inputs. It does not create agent sessions,
call model providers, execute tools, approve changes, or mutate repositories.
A review is independent only after distinct runtime context IDs are recorded.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


MAX_TITLE = 200
MAX_TEXT = 12_000
MAX_REVIEWERS = 5
MAX_EVIDENCE = 30
SEVERITIES = {"critical", "high", "medium", "low", "info"}


def _required_text(value: str, name: str, limit: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    value = value.strip()
    if len(value) > limit:
        raise ValueError(f"{name} exceeds {limit} characters")
    return value


@dataclass(frozen=True, slots=True)
class DesignBrief:
    """The complete, deliberately bounded context shared with fresh reviewers."""

    title: str
    problem: str
    intended_outcome: str
    constraints: tuple[str, ...] = ()
    acceptance_criteria: tuple[str, ...] = ()
    source_evidence: tuple[str, ...] = ()
    task_id: str | None = None
    mission_id: str | None = None

    def __post_init__(self) -> None:
        _required_text(self.title, "title", MAX_TITLE)
        _required_text(self.problem, "problem", MAX_TEXT)
        _required_text(self.intended_outcome, "intended_outcome", MAX_TEXT)
        for field_name in ("constraints", "acceptance_criteria", "source_evidence"):
            values = getattr(self, field_name)
            if not isinstance(values, tuple):
                raise ValueError(f"{field_name} must be a tuple")
            if len(values) > MAX_EVIDENCE:
                raise ValueError(f"{field_name} contains too many entries")
            for value in values:
                _required_text(value, field_name, MAX_TEXT)
        if self.task_id is not None:
            _required_text(self.task_id, "task_id", 160)
        if self.mission_id is not None:
            _required_text(self.mission_id, "mission_id", 160)


@dataclass(frozen=True, slots=True)
class ReviewerPacket:
    """A reviewer-specific payload; no prior conversation or author conclusion."""

    review_id: str
    reviewer_id: str
    brief: DesignBrief
    context_policy: str = "FRESH_CONTEXT_REQUIRED"
    forbidden_context: tuple[str, ...] = (
        "author_conversation",
        "author_chain_of_thought",
        "other_reviewer_outputs",
        "author_recommendation",
        "credentials",
        "cookies",
        "session_tokens",
    )


@dataclass(frozen=True, slots=True)
class ReviewFinding:
    title: str
    severity: str
    evidence: str
    impact: str
    recommendation: str
    confidence: float = 0.5

    def __post_init__(self) -> None:
        for name in ("title", "evidence", "impact", "recommendation"):
            _required_text(getattr(self, name), name, MAX_TEXT)
        if self.severity not in SEVERITIES:
            raise ValueError("severity must be one of: " + ", ".join(sorted(SEVERITIES)))
        if isinstance(self.confidence, bool) or not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class ReviewerResult:
    review_id: str
    reviewer_id: str
    runtime_context_id: str
    findings: tuple[ReviewFinding, ...] = ()
    completed_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def __post_init__(self) -> None:
        _required_text(self.review_id, "review_id", 160)
        _required_text(self.reviewer_id, "reviewer_id", 160)
        _required_text(self.runtime_context_id, "runtime_context_id", 240)
        if len(self.findings) > 100:
            raise ValueError("a reviewer result cannot contain more than 100 findings")
        datetime.fromisoformat(self.completed_at)


def build_reviewer_packets(
    brief: DesignBrief, reviewer_ids: tuple[str, ...], review_id: str
) -> tuple[ReviewerPacket, ...]:
    """Build 2–5 bounded reviewer packets without claiming sessions exist."""
    _required_text(review_id, "review_id", 160)
    if not isinstance(reviewer_ids, tuple) or not 2 <= len(reviewer_ids) <= MAX_REVIEWERS:
        raise ValueError(f"review requires 2 to {MAX_REVIEWERS} reviewer IDs")
    normalized = tuple(_required_text(item, "reviewer_id", 160) for item in reviewer_ids)
    if len(set(normalized)) != len(normalized):
        raise ValueError("reviewer IDs must be unique")
    return tuple(
        ReviewerPacket(review_id=review_id, reviewer_id=reviewer_id, brief=brief)
        for reviewer_id in normalized
    )


def validate_independent_results(
    packets: tuple[ReviewerPacket, ...], results: tuple[ReviewerResult, ...]
) -> dict[str, Any]:
    """Verify result-to-packet mapping and distinct runtime contexts.

    This verifies recorded context identifiers only; the runtime must guarantee
    that those identifiers represent genuinely fresh, isolated model sessions.
    """
    if len(packets) < 2 or len(results) != len(packets):
        return {"independent": False, "reason": "reviewer_result_count_mismatch"}
    expected = {(p.review_id, p.reviewer_id) for p in packets}
    actual = {(r.review_id, r.reviewer_id) for r in results}
    if len(expected) != len(packets) or actual != expected:
        return {"independent": False, "reason": "reviewer_identity_mismatch"}
    context_ids = [r.runtime_context_id for r in results]
    if len(set(context_ids)) != len(context_ids):
        return {"independent": False, "reason": "shared_runtime_context"}
    return {
        "independent": True,
        "review_id": packets[0].review_id,
        "reviewer_count": len(packets),
        "distinct_runtime_contexts": len(set(context_ids)),
        "runtime_isolation_attestation_required": True,
    }


def result_to_dict(result: ReviewerResult) -> dict[str, Any]:
    """Return a JSON-ready immutable snapshot for a durable task receipt."""
    return asdict(result)
