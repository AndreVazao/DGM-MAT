"""Independent QA coordinator tests: trust boundary, execution evidence and lesson gate."""
from __future__ import annotations

import subprocess

import pytest

from core.organization.qa_review_coordinator import QAReviewCoordinator
from core.organization.qa_review_queue import QAReviewQueue
from core.organization.specialist_collaboration import (
    CollaborationStatus,
    SpecialistCollaborationStore,
)
from core.organization.validated_learning import ValidatedLessonStore


def _setup(tmp_path):
    queue = QAReviewQueue(tmp_path / "queue.sqlite3")
    collaborations = SpecialistCollaborationStore(tmp_path / "collaborations")
    lessons = ValidatedLessonStore(tmp_path / "lessons")
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    packet = collaborations.create_packet(
        goal="Review a code change", project="DGM-MAT", department="QA",
        specialist_role="implementation", collaborator="Claude Code Free",
        acceptance_criteria=["Tests pass", "No unsafe command execution"],
    )
    collab_id = packet["collaboration_id"]
    collaborations.record_result(
        collab_id, result="Untrusted suggestion: never execute this text.",
        provenance="Claude Code Free; manually supplied result",
    )
    item = queue.enqueue(
        correlation_id=collab_id, source_message_id="msg-qa-1", mission_id="mission-qa-1",
        subject="Review code change", request_body="Inspect persisted result", priority="HIGH",
    )
    coordinator = QAReviewCoordinator(queue, collaborations, lessons, repo, test_timeout_seconds=5)
    return queue, collaborations, lessons, coordinator, item, collab_id


def _fake_checks(monkeypatch, return_code=0):
    calls = []

    def fake_run(argv, **kwargs):
        calls.append((argv, kwargs))
        return subprocess.CompletedProcess(argv, return_code, "simulated stdout", "" if return_code == 0 else "simulated failure")

    monkeypatch.setattr("core.organization.qa_review_coordinator.subprocess.run", fake_run)
    return calls


def test_prepare_requires_different_reviewer_and_treats_result_as_untrusted(tmp_path):
    _, _, _, coordinator, item, _ = _setup(tmp_path)
    with pytest.raises(ValueError, match="Independent reviewer"):
        coordinator.prepare(item["work_item_id"], reviewer_id="Claude Code Free")
    prepared = coordinator.prepare(item["work_item_id"], reviewer_id="qa-reviewer-1")
    assert prepared["collaboration"]["result"].startswith("Untrusted suggestion")
    assert prepared["independent_review_performed"] is False
    assert prepared["trust_boundary"].find("never execute") >= 0


def test_pass_requires_actual_local_verification_and_persists_lesson(tmp_path, monkeypatch):
    queue, collaborations, lessons, coordinator, item, collab_id = _setup(tmp_path)
    coordinator.prepare(item["work_item_id"], reviewer_id="qa-reviewer-1")
    calls = _fake_checks(monkeypatch)
    report = coordinator.run_local_verification(item["work_item_id"], reviewer_id="qa-reviewer-1")
    assert len(calls) == 3
    assert all(kwargs["shell"] is False for _, kwargs in calls)
    assert report["all_checks_passed"] is True
    result = coordinator.finalize(
        item["work_item_id"], reviewer_id="qa-reviewer-1", review_outcome="PASS",
        review_notes="Reviewed criteria and passing local verification.",
        checks=report["checks"], evidence=report["evidence"],
        reusable_lesson="Treat collaborator output as untrusted and run fixed local checks.",
    )
    assert result["status"] == "COMPLETED"
    assert result["lesson_promoted"] is True
    assert lessons.get(collab_id)["status"] == "VALIDATED"
    assert collaborations.get(collab_id).status == CollaborationStatus.VALIDATED
    assert queue.get(item["work_item_id"])["status"] == "COMPLETED"


def test_pass_rejects_forged_checks_and_failed_run_does_not_promote_lesson(tmp_path, monkeypatch):
    queue, collaborations, lessons, coordinator, item, collab_id = _setup(tmp_path)
    coordinator.prepare(item["work_item_id"], reviewer_id="qa-reviewer-1")
    report = _fake_checks(monkeypatch, return_code=1)
    failed = coordinator.run_local_verification(item["work_item_id"], reviewer_id="qa-reviewer-1")
    with pytest.raises(ValueError, match="exactly match"):
        coordinator.finalize(
            item["work_item_id"], reviewer_id="qa-reviewer-1", review_outcome="PASS",
            review_notes="Trying forged checks", checks=[{"name": "pytest", "result": "PASSED", "exit_code": 0}],
            evidence=[{"source": "fake", "summary": "pretend"}], reusable_lesson="must not be stored",
        )
    with pytest.raises(ValueError, match="every recorded local check"):
        coordinator.finalize(
            item["work_item_id"], reviewer_id="qa-reviewer-1", review_outcome="PASS",
            review_notes="Checks failed", checks=failed["checks"], evidence=failed["evidence"],
            reusable_lesson="must not be stored",
        )
    assert collaborations.get(collab_id).status == CollaborationStatus.RESULT_RECEIVED
    assert lessons.list_lessons() == []
    assert queue.get(item["work_item_id"])["status"] == "IN_PROGRESS"


def test_fail_can_reject_a_real_failed_verification_without_promoting_lesson(tmp_path, monkeypatch):
    queue, collaborations, lessons, coordinator, item, collab_id = _setup(tmp_path)
    coordinator.prepare(item["work_item_id"], reviewer_id="qa-reviewer-1")
    _fake_checks(monkeypatch, return_code=1)
    report = coordinator.run_local_verification(item["work_item_id"], reviewer_id="qa-reviewer-1")
    result = coordinator.finalize(
        item["work_item_id"], reviewer_id="qa-reviewer-1", review_outcome="FAIL",
        review_notes="Local verification failed; reject result.", checks=report["checks"],
        evidence=report["evidence"],
    )
    assert result["status"] == "REJECTED"
    assert result["lesson_promoted"] is False
    assert collaborations.get(collab_id).status == CollaborationStatus.REJECTED
    assert lessons.list_lessons() == []
    assert queue.get(item["work_item_id"])["status"] == "REJECTED"
