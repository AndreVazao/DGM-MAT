"""Host-runtime coordinator for genuinely isolated, read-only EGM reviews.

A host-owned adapter creates provider sessions with fresh context and tools
disabled. This coordinator never launches a provider itself, never shares
reviewer output between sessions, and persists only a task-linked receipt.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Protocol

from .design_review import (
    DesignBrief,
    ReviewFinding,
    ReviewerPacket,
    ReviewerResult,
    build_reviewer_packets,
    validate_independent_results,
)
from .models import TaskStatus
from .task_manager import OrganizationTaskManager


COORDINATOR_AGENT_ID = "agent:design-review-coordinator"
TASK_KIND = "independent_design_review"
ATTESTATION_ISSUER = "dgm_mat_host_runtime"


@dataclass(frozen=True, slots=True)
class RuntimeIsolationAttestation:
    """Host-runtime evidence that a reviewer session is fresh and tool-less."""

    issuer: str
    runtime_context_id: str
    fresh_session: bool
    prior_history_excluded: bool
    cross_reviewer_context_disabled: bool
    tools_disabled: bool
    write_access_disabled: bool
    credentials_excluded: bool

    def __post_init__(self) -> None:
        if self.issuer != ATTESTATION_ISSUER:
            raise ValueError("runtime_attestation_issuer_invalid")
        if not isinstance(self.runtime_context_id, str) or not self.runtime_context_id.strip():
            raise ValueError("runtime_context_id_required")
        required = (
            self.fresh_session,
            self.prior_history_excluded,
            self.cross_reviewer_context_disabled,
            self.tools_disabled,
            self.write_access_disabled,
            self.credentials_excluded,
        )
        if any(value is not True for value in required):
            raise ValueError("runtime_isolation_policy_not_satisfied")


class ReviewSession(Protocol):
    """Minimal no-tools reviewer surface implemented by a trusted host adapter."""

    @property
    def runtime_context_id(self) -> str: ...

    @property
    def isolation_attestation(self) -> RuntimeIsolationAttestation: ...

    def review(self, packet: ReviewerPacket) -> tuple[ReviewFinding, ...]: ...


class ReviewSessionFactory(Protocol):
    """Creates a new provider conversation with history and tools disabled."""

    def create_fresh_session(self, packet: ReviewerPacket) -> ReviewSession: ...


@dataclass(frozen=True, slots=True)
class DesignReviewExecution:
    status: str
    task_id: str
    review_id: str
    independent: bool
    reviewer_count: int
    receipt_message_id: str | None = None
    reason: str | None = None
    receipt: dict[str, Any] | None = None


class DesignReviewCoordinator:
    """Run independent reviews and persist the result in the existing task record."""

    def __init__(
        self,
        tasks: OrganizationTaskManager,
        session_factory: ReviewSessionFactory,
    ) -> None:
        if not isinstance(tasks, OrganizationTaskManager):
            raise TypeError("OrganizationTaskManager is required")
        if not callable(getattr(session_factory, "create_fresh_session", None)):
            raise TypeError("a host-owned fresh-session factory is required")
        self.tasks = tasks
        self.session_factory = session_factory

    @staticmethod
    def _validate_task(task: Any, brief: DesignBrief) -> str | None:
        if task is None:
            return "review_task_not_found"
        if task.status != TaskStatus.RUNNING:
            return "review_task_not_running"
        if task.assigned_agent != COORDINATOR_AGENT_ID:
            return "review_task_not_assigned_to_coordinator"
        if not isinstance(task.metadata, dict) or task.metadata.get("task_kind") != TASK_KIND:
            return "review_task_kind_not_allowed"
        if brief.task_id != task.task_id or brief.mission_id != task.mission_id:
            return "review_brief_task_binding_mismatch"
        return None

    def run(
        self,
        *,
        task_id: str,
        brief: DesignBrief,
        reviewer_ids: tuple[str, ...],
        review_id: str,
    ) -> DesignReviewExecution:
        """Create all fresh contexts first, review independently, then persist once."""
        if not self.tasks.durable_persistence_enabled:
            return DesignReviewExecution(
                "BLOCKED", task_id, review_id, False, 0,
                reason="durable_task_persistence_required",
            )
        task = self.tasks.get(task_id)
        reason = self._validate_task(task, brief)
        if reason:
            return DesignReviewExecution("BLOCKED", task_id, review_id, False, 0, reason=reason)

        try:
            packets = build_reviewer_packets(brief, reviewer_ids, review_id)
        except (TypeError, ValueError) as exc:
            return DesignReviewExecution(
                "BLOCKED",
                task_id,
                review_id,
                False,
                0,
                reason=f"invalid_review_packet:{str(exc)[:180]}",
            )

        sessions: list[ReviewSession] = []
        try:
            # Create every session before sending any review request.
            for packet in packets:
                session = self.session_factory.create_fresh_session(packet)
                if session is None or not callable(getattr(session, "review", None)):
                    raise ValueError("review_session_invalid")
                sessions.append(session)

            if len({id(session) for session in sessions}) != len(sessions):
                raise ValueError("review_session_object_reused")

            attestations: list[RuntimeIsolationAttestation] = []
            context_ids: list[str] = []
            for session in sessions:
                attestation = session.isolation_attestation
                if not isinstance(attestation, RuntimeIsolationAttestation):
                    raise ValueError("runtime_isolation_attestation_missing")
                if session.runtime_context_id != attestation.runtime_context_id:
                    raise ValueError("runtime_context_attestation_mismatch")
                attestations.append(attestation)
                context_ids.append(attestation.runtime_context_id)

            if len(set(context_ids)) != len(context_ids):
                raise ValueError("shared_runtime_context")

            # Each reviewer receives only its own packet; no cross-review synthesis
            # is sent back into any reviewer session.
            results: list[ReviewerResult] = []
            for packet, session, context_id in zip(packets, sessions, context_ids):
                findings = session.review(packet)
                if not isinstance(findings, tuple):
                    raise ValueError("review_findings_must_be_tuple")
                if any(not isinstance(item, ReviewFinding) for item in findings):
                    raise ValueError("review_finding_schema_invalid")
                results.append(
                    ReviewerResult(
                        review_id=review_id,
                        reviewer_id=packet.reviewer_id,
                        runtime_context_id=context_id,
                        findings=findings,
                    )
                )

            validation = validate_independent_results(
                packets,
                tuple(results),
                runtime_isolation_attested=True,
            )
            if validation.get("independent") is not True:
                raise ValueError(validation.get("reason", "review_independence_failed"))

            receipt = {
                "schema_version": 1,
                "kind": "elephant_goldfish_independent_review",
                "task_id": task_id,
                "mission_id": task.mission_id,
                "review_id": review_id,
                "independence": validation,
                "runtime_attestations": [asdict(item) for item in attestations],
                "reviewer_results": [
                    {
                        "review_id": item.review_id,
                        "reviewer_id": item.reviewer_id,
                        "runtime_context_id": item.runtime_context_id,
                        "completed_at": item.completed_at,
                        "findings": [asdict(finding) for finding in item.findings],
                    }
                    for item in results
                ],
                "authority": {
                    "read_only": True,
                    "tools_enabled": False,
                    "write_access_enabled": False,
                    "automatic_approval": False,
                    "automatic_execution": False,
                },
            }
            message_id = f"egm-review:{review_id}"
            completed = self.tasks.complete_with_result(
                task_id, result=receipt, message_id=message_id
            )
            return DesignReviewExecution(
                "COMPLETED",
                task_id,
                review_id,
                True,
                len(results),
                receipt_message_id=message_id,
                receipt=completed.metadata["worker_execution"]["result"],
            )
        except Exception as exc:
            # Keep the task RUNNING and without a success receipt. A supervisor
            # can inspect/recover it; never convert an incomplete review to success.
            return DesignReviewExecution(
                "FAILED",
                task_id,
                review_id,
                False,
                len(sessions),
                reason=f"{type(exc).__name__}:{str(exc)[:240]}",
            )
