"""Tests for host-attested, read-only independent design review execution."""
import pytest

from core.organization.design_review import DesignBrief, ReviewFinding
from core.organization.design_review_coordinator import (
    ATTESTATION_ISSUER,
    COORDINATOR_AGENT_ID,
    TASK_KIND,
    DesignReviewCoordinator,
    RuntimeIsolationAttestation,
)
from core.organization.message_bus import InternalMessageBus
from core.organization.models import Task, TaskStatus
from core.organization.task_manager import OrganizationTaskManager


def make_attestation(context_id):
    return RuntimeIsolationAttestation(
        issuer=ATTESTATION_ISSUER,
        runtime_context_id=context_id,
        fresh_session=True,
        prior_history_excluded=True,
        cross_reviewer_context_disabled=True,
        tools_disabled=True,
        write_access_disabled=True,
        credentials_excluded=True,
    )


class FakeSession:
    def __init__(self, context_id, findings=()):
        self.runtime_context_id = context_id
        self.isolation_attestation = make_attestation(context_id)
        self.findings = findings
        self.received = []

    def review(self, packet):
        self.received.append(packet)
        return self.findings


class FakeFactory:
    def __init__(self, *, shared=False, findings=()):
        self.shared = shared
        self.findings = findings
        self.sessions = []

    def create_fresh_session(self, packet):
        context_id = "ctx:shared" if self.shared else f"ctx:{packet.reviewer_id}"
        session = FakeSession(context_id, self.findings)
        self.sessions.append(session)
        return session


def setup_task(tmp_path, *, durable=True, status=TaskStatus.RUNNING, task_kind=TASK_KIND):
    tmp_path.mkdir(parents=True, exist_ok=True)
    bus = InternalMessageBus(tmp_path / "organization.sqlite3") if durable else None
    manager = OrganizationTaskManager(bus)
    task = Task(
        task_id="task:egm-review",
        title="Independent design review",
        mission_id="mission:egm",
        description="Review a bounded design brief without changing code.",
        assigned_agent=COORDINATOR_AGENT_ID,
        status=status,
        metadata={"task_kind": task_kind},
    )
    manager.create(task)
    return bus, manager


def make_brief():
    return DesignBrief(
        title="Review archive search design",
        problem="Conversation archive search may lose provenance.",
        intended_outcome="Preserve source identity across imports.",
        constraints=("Local-first", "Read-only review"),
        acceptance_criteria=("Every result has a stable source locator",),
        source_evidence=("docs/archive.md#L10-L20",),
        task_id="task:egm-review",
        mission_id="mission:egm",
    )


def test_coordinator_runs_fresh_reviewers_and_persists_existing_task_receipt(tmp_path):
    bus, manager = setup_task(tmp_path)
    finding = ReviewFinding(
        title="Source identity needs a uniqueness rule",
        severity="high",
        evidence="The brief does not define provider/source ID uniqueness.",
        impact="Re-imports could create ambiguous duplicate conversations.",
        recommendation="Define a stable compound key and collision policy.",
        confidence=0.9,
    )
    factory = FakeFactory(findings=(finding,))
    coordinator = DesignReviewCoordinator(manager, factory)

    result = coordinator.run(
        task_id="task:egm-review",
        brief=make_brief(),
        reviewer_ids=("reviewer:security", "reviewer:data"),
        review_id="review:archive-001",
    )

    assert result.status == "COMPLETED"
    assert result.independent is True
    assert result.reviewer_count == 2
    assert len(factory.sessions) == 2
    assert factory.sessions[0] is not factory.sessions[1]
    assert factory.sessions[0].received[0].reviewer_id == "reviewer:security"
    assert factory.sessions[1].received[0].reviewer_id == "reviewer:data"
    task = manager.get("task:egm-review")
    assert task.status is TaskStatus.COMPLETED
    receipt = task.metadata["worker_execution"]["result"]
    assert receipt["kind"] == "elephant_goldfish_independent_review"
    assert receipt["authority"]["tools_enabled"] is False
    assert receipt["authority"]["automatic_execution"] is False
    assert len(receipt["runtime_attestations"]) == 2
    assert receipt["independence"]["runtime_isolation_attested"] is True
    bus.close()


def test_non_durable_task_manager_is_blocked_before_session_creation(tmp_path):
    _bus, manager = setup_task(tmp_path, durable=False)
    factory = FakeFactory()
    result = DesignReviewCoordinator(manager, factory).run(
        task_id="task:egm-review",
        brief=make_brief(),
        reviewer_ids=("reviewer:a", "reviewer:b"),
        review_id="review:non-durable",
    )
    assert result.status == "BLOCKED"
    assert result.reason == "durable_task_persistence_required"
    assert factory.sessions == []


def test_shared_context_is_rejected_without_completing_task(tmp_path):
    bus, manager = setup_task(tmp_path)
    factory = FakeFactory(shared=True)
    result = DesignReviewCoordinator(manager, factory).run(
        task_id="task:egm-review",
        brief=make_brief(),
        reviewer_ids=("reviewer:a", "reviewer:b"),
        review_id="review:shared",
    )
    assert result.status == "FAILED"
    assert result.reason.startswith("ValueError:shared_runtime_context")
    assert manager.get("task:egm-review").status is TaskStatus.RUNNING
    assert "worker_execution" not in manager.get("task:egm-review").metadata
    bus.close()


@pytest.mark.parametrize(
    "field",
    [
        "fresh_session",
        "prior_history_excluded",
        "cross_reviewer_context_disabled",
        "tools_disabled",
        "write_access_disabled",
        "credentials_excluded",
    ],
)
def test_runtime_attestation_rejects_any_unsafe_policy(field):
    values = {
        "issuer": ATTESTATION_ISSUER,
        "runtime_context_id": "ctx:reviewer",
        "fresh_session": True,
        "prior_history_excluded": True,
        "cross_reviewer_context_disabled": True,
        "tools_disabled": True,
        "write_access_disabled": True,
        "credentials_excluded": True,
    }
    values[field] = False
    with pytest.raises(ValueError, match="runtime_isolation_policy_not_satisfied"):
        RuntimeIsolationAttestation(**values)


def test_task_binding_mismatch_never_creates_sessions(tmp_path):
    bus, manager = setup_task(tmp_path)
    factory = FakeFactory()
    brief = DesignBrief(
        title="Mismatch",
        problem="Wrong task binding",
        intended_outcome="Must fail closed",
        task_id="task:other",
        mission_id="mission:egm",
    )
    result = DesignReviewCoordinator(manager, factory).run(
        task_id="task:egm-review",
        brief=brief,
        reviewer_ids=("reviewer:a", "reviewer:b"),
        review_id="review:mismatch",
    )
    assert result.status == "BLOCKED"
    assert result.reason == "review_brief_task_binding_mismatch"
    assert factory.sessions == []
    bus.close()


def test_invalid_task_kind_and_state_are_blocked(tmp_path):
    bus, manager = setup_task(tmp_path, task_kind="arbitrary")
    result = DesignReviewCoordinator(manager, FakeFactory()).run(
        task_id="task:egm-review",
        brief=make_brief(),
        reviewer_ids=("reviewer:a", "reviewer:b"),
        review_id="review:wrong-kind",
    )
    assert result.status == "BLOCKED"
    assert result.reason == "review_task_kind_not_allowed"
    bus.close()

    bus, manager = setup_task(tmp_path / "other", status=TaskStatus.ASSIGNED)
    result = DesignReviewCoordinator(manager, FakeFactory()).run(
        task_id="task:egm-review",
        brief=make_brief(),
        reviewer_ids=("reviewer:a", "reviewer:b"),
        review_id="review:wrong-state",
    )
    assert result.status == "BLOCKED"
    assert result.reason == "review_task_not_running"
    bus.close()
