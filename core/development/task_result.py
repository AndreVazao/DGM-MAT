"""Shared, fail-closed result contract for DGM-MAT development tasks.

A task plan or successful API call is not proof of implementation. The VERIFIED
state requires explicit validation and independent QA evidence. This module is
deliberately side-effect-free and does not execute tools or persist state.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class TaskResultStatus(str, Enum):
    PLANNED = "planned"
    BLOCKED = "blocked"
    NOT_IMPLEMENTED = "not_implemented"
    RUNNING = "running"
    FAILED = "failed"
    VERIFIED = "verified"


@dataclass(frozen=True)
class TaskEvidence:
    """A concise pointer to evidence; do not place secrets or full logs here."""

    kind: str
    outcome: str
    reference: str
    detail: str = ""

    def __post_init__(self) -> None:
        for field_name in ("kind", "outcome", "reference", "detail"):
            value = getattr(self, field_name)
            if not isinstance(value, str):
                raise ValueError(f"evidence {field_name} must be a string.")
        if not self.kind.strip() or not self.outcome.strip() or not self.reference.strip():
            raise ValueError("evidence kind, outcome, and reference must be non-empty.")


@dataclass(frozen=True)
class DevelopmentTaskResult:
    """Truthful terminal/intermediate state shared by planning and execution layers."""

    task_id: str
    status: TaskResultStatus
    summary: str
    evidence: tuple[TaskEvidence, ...] = field(default_factory=tuple)
    validation_passed: bool = False
    independent_qa_passed: bool = False
    commit_sha: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.task_id, str) or not self.task_id.strip():
            raise ValueError("task_id must be a non-empty string.")
        if not isinstance(self.summary, str) or not self.summary.strip():
            raise ValueError("summary must be a non-empty string.")
        if not isinstance(self.status, TaskResultStatus):
            raise ValueError("status must be a TaskResultStatus value.")
        if self.commit_sha is not None:
            sha = self.commit_sha.strip()
            if len(sha) not in (40, 64) or any(c not in "0123456789abcdefABCDEF" for c in sha):
                raise ValueError("commit_sha must be a full 40- or 64-character hexadecimal hash.")
        if self.status is TaskResultStatus.VERIFIED:
            if not self.validation_passed:
                raise ValueError("verified status requires validation_passed=True.")
            if not self.independent_qa_passed:
                raise ValueError("verified status requires independent_qa_passed=True.")
            required_kinds = {item.kind for item in self.evidence}
            if not {"validation", "independent_qa"}.issubset(required_kinds):
                raise ValueError("verified status requires validation and independent_qa evidence references.")
            required_evidence = {
                item.kind: item
                for item in self.evidence
                if item.kind in {"validation", "independent_qa"}
            }
            if any(
                required_evidence[kind].outcome.strip().casefold() != "passed"
                for kind in ("validation", "independent_qa")
            ):
                raise ValueError("verified status requires both validation and independent QA evidence outcomes to be 'passed'.")
        elif self.validation_passed or self.independent_qa_passed:
            raise ValueError("pass flags may only be set when status is verified.")

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-friendly representation without inferring success."""
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "summary": self.summary,
            "evidence": [
                {
                    "kind": item.kind,
                    "outcome": item.outcome,
                    "reference": item.reference,
                    "detail": item.detail,
                }
                for item in self.evidence
            ],
            "validation_passed": self.validation_passed,
            "independent_qa_passed": self.independent_qa_passed,
            "commit_sha": self.commit_sha,
        }
