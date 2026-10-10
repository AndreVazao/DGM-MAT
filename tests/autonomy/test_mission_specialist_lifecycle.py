"""MissionEngine integration tests for specialist results and validated learning."""
import pytest

from core.autonomy.mission_engine import MissionEngine
from core.organization.message_bus import InternalMessageBus
from core.autonomy.mission_models import Mission
from core.organization.specialist_collaboration import (
    CollaborationStatus,
    SpecialistCollaborationStore,
)
from core.organization.validated_learning import ValidatedLessonStore


def make_engine(tmp_path, monkeypatch):
    engine = MissionEngine(organization_bus=InternalMessageBus())
    engine.collaboration_store = SpecialistCollaborationStore(tmp_path / "collaborations")
    engine.validated_lesson_store = ValidatedLessonStore(tmp_path / "lessons")
    monkeypatch.setattr(engine, "save_mission", lambda mission: None)
    monkeypatch.setattr(engine, "_sync_state", lambda mission: None)
    mission = Mission(
        mission_id="mission_collaboration_lifecycle_test",
        goal="Improve specialist collaboration workflow",
        description="Exercise the end-to-end local review lifecycle.",
        metadata={"project_id": "DGM-MAT"},
    )
    engine.active_missions[mission.mission_id] = mission
    packet = engine.prepare_specialist_collaboration(mission.mission_id)
    return engine, mission, packet


def test_result_is_untrusted_then_independently_reviewed_and_persisted_as_lesson(tmp_path, monkeypatch):
    engine, mission, packet = make_engine(tmp_path, monkeypatch)
    collaboration_id = packet["collaboration_id"]

    received = engine.record_specialist_result(
        collaboration_id,
        result="Add a durable validation boundary and preserve provenance.",
        provenance="Claude Code Free; user-authorized session; free mode confirmed by operator.",
    )
    assert received["status"] == CollaborationStatus.RESULT_RECEIVED.value
    assert received["review_required"] is True
    assert received["external_call_performed"] is False
    assert mission.metadata["specialist_collaboration"]["status"] == "RESULT_RECEIVED"

    review_messages = engine.organization_bus.receive("agent:bug-hunter", unread_only=True)
    assert len(review_messages) == 1
    assert review_messages[0].correlation_id == collaboration_id
    assert review_messages[0].requires_response is True

    validated = engine.validate_specialist_result(
        collaboration_id,
        reviewer="agent:bug-hunter",
        review_notes="Inspected the stored result and checked the implementation against the acceptance criteria.",
        evidence=["Local focused pytest suite: 3 passed", "git diff --check: passed"],
        tests_passed=True,
        reusable_lesson="Store collaborator output as untrusted; only promote a reusable lesson after independent review and passing local verification.",
    )
    assert validated["status"] == CollaborationStatus.VALIDATED.value
    assert validated["lesson_status"] == "PERSISTED"
    assert validated["lesson_id"] == f"lesson_{collaboration_id}"
    assert mission.metadata["specialist_collaboration"]["lesson_status"] == "PERSISTED"

    lessons = engine.list_validated_specialist_lessons(project="DGM-MAT")
    assert len(lessons) == 1
    assert lessons[0]["status"] == "VALIDATED"
    assert lessons[0]["source_collaborator"] == "Claude Code Free"
    assert "only promote a reusable lesson" in lessons[0]["lesson"]


def test_unverified_or_same_collaborator_result_cannot_become_a_lesson(tmp_path, monkeypatch):
    engine, _, packet = make_engine(tmp_path, monkeypatch)
    collaboration_id = packet["collaboration_id"]
    engine.record_specialist_result(
        collaboration_id,
        result="Proposed change",
        provenance="Claude Code Free",
    )

    with pytest.raises(ValueError, match="tests_passed"):
        engine.validate_specialist_result(
            collaboration_id,
            reviewer="agent:bug-hunter",
            review_notes="No tests were run.",
            evidence=["Code inspection only"],
            tests_passed=False,
            reusable_lesson="Must not be promoted.",
        )
    with pytest.raises(ValueError, match="Independent reviewer"):
        engine.validate_specialist_result(
            collaboration_id,
            reviewer="Claude Code Free",
            review_notes="Self review is not independent.",
            evidence=["Tests claimed by original collaborator"],
            tests_passed=True,
            reusable_lesson="Must not be promoted.",
        )
    assert engine.list_validated_specialist_lessons() == []


def test_validated_lesson_persistence_failure_can_be_retried_without_revalidating(tmp_path, monkeypatch):
    engine, _, packet = make_engine(tmp_path, monkeypatch)
    collaboration_id = packet["collaboration_id"]
    engine.record_specialist_result(
        collaboration_id,
        result="A verified result that can be learned from.",
        provenance="Local specialist; no external call.",
    )
    original_record = engine.validated_lesson_store.record
    monkeypatch.setattr(
        engine.validated_lesson_store,
        "record",
        lambda _packet: (_ for _ in ()).throw(OSError("simulated storage failure")),
    )

    first = engine.validate_specialist_result(
        collaboration_id,
        reviewer="agent:bug-hunter",
        review_notes="Independent review complete.",
        evidence=["Focused local tests passed"],
        tests_passed=True,
        reusable_lesson="Persist validated lessons idempotently and make failures retryable.",
    )
    assert first["status"] == CollaborationStatus.VALIDATED.value
    assert first["lesson_status"] == "PERSISTENCE_FAILED"
    assert engine.list_validated_specialist_lessons() == []

    monkeypatch.setattr(engine.validated_lesson_store, "record", original_record)
    recovered = engine.retry_validated_lesson_persistence(collaboration_id)
    assert recovered["lesson_status"] == "PERSISTED"
    assert len(engine.list_validated_specialist_lessons()) == 1


def test_free_capacity_pause_is_persisted_without_paid_fallback(tmp_path, monkeypatch):
    engine, mission, packet = make_engine(tmp_path, monkeypatch)
    paused = engine.pause_specialist_collaboration(
        packet["collaboration_id"], reason="Free tier limit reached; wait for reset."
    )
    assert paused["status"] == CollaborationStatus.WAITING_FOR_FREE_CAPACITY.value
    assert paused["paid_fallback"] is False
    assert mission.metadata["specialist_collaboration"]["status"] == "WAITING_FOR_FREE_CAPACITY"
