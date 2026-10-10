from datetime import datetime, timedelta

import pytest

from core.autonomy.mission_engine import MissionEngine
from core.autonomy.mission_models import MissionStatus
from core.organization.human_intervention_queue import HumanInterventionQueue


def isolated_engine(tmp_path):
    engine = MissionEngine()
    engine.active_missions.clear()
    engine.missions_path = tmp_path / "missions"
    engine.missions_path.mkdir(parents=True, exist_ok=True)
    engine.human_intervention_queue = HumanInterventionQueue(tmp_path / "interventions.sqlite3")
    return engine


def test_waiting_mission_is_persisted_and_does_not_timeout_or_block_scheduler(tmp_path):
    engine = isolated_engine(tmp_path)
    waiting = engine.create_mission("Human checkpoint test", "Pause this mission")
    request = engine.request_human_intervention(
        waiting.mission_id,
        step_id="confirm-login",
        reason="Operator must complete a legitimate sign-in",
        instructions="Complete the sign-in manually, then return to this request.",
    )
    waiting.created_at = datetime.now() - timedelta(days=2)
    engine.save_mission(waiting)

    other = engine.create_mission("Independent work test", "Must remain schedulable")
    engine.process_missions()

    assert waiting.status == MissionStatus.WAITING_FOR_USER
    assert engine.human_intervention_queue.get_request(request["request_id"])["status"] == "WAITING_FOR_USER"
    assert other.status == MissionStatus.QUEUED


def test_subtasks_survive_engine_recreation(tmp_path):
    engine = isolated_engine(tmp_path)
    mission = engine.create_mission("Persist subtasks test", "Persist the checkpoint")
    engine.decompose_mission(mission.mission_id)
    expected_ids = [item.subtask_id for item in mission.subtasks]
    expected_statuses = [item.status for item in mission.subtasks]

    recovered = isolated_engine(tmp_path)
    recovered._load_missions()
    restored = recovered.active_missions[mission.mission_id]
    assert [item.subtask_id for item in restored.subtasks] == expected_ids
    assert [item.status for item in restored.subtasks] == expected_statuses


def test_resume_requires_accepted_decision_and_verified_real_state(tmp_path):
    engine = isolated_engine(tmp_path)
    mission = engine.create_mission("Verified resume test", "Never resume blindly")
    request = engine.request_human_intervention(
        mission.mission_id,
        step_id="external-state-check",
        reason="The external result needs manual confirmation",
        instructions="Complete the action manually and verify its actual result.",
    )
    request_id = request["request_id"]
    assert engine.human_intervention_queue.submit_decision(
        request_id,
        mission_id=mission.mission_id,
        step_id="external-state-check",
        decision="APPROVE",
        actor_id="test-local-operator",
    )

    with pytest.raises(ValueError, match="decision actor"):
        engine.resolve_human_intervention(mission.mission_id, request_id, verified=True, verification_evidence="not authorized", actor_id="different-operator")
    with pytest.raises(ValueError, match="real external state is verified"):
        engine.resolve_human_intervention(mission.mission_id, request_id, verified=False, actor_id="test-local-operator")
    assert mission.status == MissionStatus.WAITING_FOR_USER

    result = engine.resolve_human_intervention(
        mission.mission_id,
        request_id,
        verified=True,
        verification_evidence="Local verifier confirmed the expected post-action state.",
        actor_id="test-local-operator",
    )
    assert result["status"] == "RUNNING"
    assert mission.status == MissionStatus.RUNNING
    assert engine.human_intervention_queue.get_request(request_id)["status"] == "RESUMED"


def test_rejected_handoff_cancels_mission_and_cannot_be_replayed(tmp_path):
    engine = isolated_engine(tmp_path)
    mission = engine.create_mission("Cancellation test", "Respect rejection")
    request = engine.request_human_intervention(
        mission.mission_id,
        step_id="sensitive-action-confirm",
        reason="Explicit operator decision required",
        instructions="Review the proposed action and choose approve or cancel.",
    )
    request_id = request["request_id"]
    assert engine.human_intervention_queue.submit_decision(
        request_id,
        mission_id=mission.mission_id,
        step_id="sensitive-action-confirm",
        decision="REJECT",
        actor_id="test-local-operator",
    )
    result = engine.resolve_human_intervention(mission.mission_id, request_id, verified=False, actor_id="test-local-operator")
    assert result["status"] == "CANCELLED"
    assert mission.status == MissionStatus.CANCELLED
    with pytest.raises(ValueError, match="active handoff"):
        engine.resolve_human_intervention(mission.mission_id, request_id, verified=True, verification_evidence="stale")


def test_orphaned_queue_request_is_reconciled_after_crash(tmp_path):
    engine = isolated_engine(tmp_path)
    mission = engine.create_mission("Crash reconciliation test", "Recover a durable request")
    mission.status = MissionStatus.RUNNING
    engine.save_mission(mission)
    request = engine.human_intervention_queue.create_request(
        mission_id=mission.mission_id,
        step_id="crash-window-step",
        reason="A human must confirm the external state",
        instructions="Complete the required step manually and confirm the outcome.",
    )

    recovered = isolated_engine(tmp_path)
    recovered._load_missions()
    restored = recovered.active_missions[mission.mission_id]
    assert restored.status == MissionStatus.WAITING_FOR_USER
    assert restored.metadata["human_intervention"]["request_id"] == request["request_id"]
    assert restored.metadata["human_intervention"]["recovered_after_restart"] is True


def test_verified_resume_pending_finalize_recovers_after_restart(tmp_path):
    engine = isolated_engine(tmp_path)
    mission = engine.create_mission("Resume recovery test", "Recover a verified checkpoint")
    request = engine.request_human_intervention(
        mission.mission_id,
        step_id="recover-resume",
        reason="Confirm the real external result",
        instructions="Perform the action manually and verify its result.",
    )
    request_id = request["request_id"]
    assert engine.human_intervention_queue.submit_decision(
        request_id,
        mission_id=mission.mission_id,
        step_id="recover-resume",
        decision="APPROVE",
        actor_id="test-local-operator",
    )
    assert engine.human_intervention_queue.mark_verifying(request_id)
    verified_at = datetime.now().isoformat()
    mission.metadata["human_intervention"].update({
        "status": "RESUME_VERIFIED_PENDING_FINALIZE",
        "resume_verified_at": verified_at,
        "verification_evidence": "The expected external state was confirmed by the local verifier.",
    })
    engine.save_mission(mission)

    recovered = isolated_engine(tmp_path)
    recovered._load_missions()
    restored = recovered.active_missions[mission.mission_id]
    assert restored.status == MissionStatus.RUNNING
    assert restored.metadata["human_intervention"]["status"] == "RESUMED"
    assert recovered.human_intervention_queue.get_request(request_id)["status"] == "RESUMED"


def test_interrupted_verification_claim_requires_verification_again(tmp_path):
    engine = isolated_engine(tmp_path)
    mission = engine.create_mission("Verification recovery test", "Never assume external state")
    request = engine.request_human_intervention(
        mission.mission_id,
        step_id="retry-verification",
        reason="Verify external state",
        instructions="Check the real outcome before resuming.",
    )
    request_id = request["request_id"]
    assert engine.human_intervention_queue.submit_decision(
        request_id,
        mission_id=mission.mission_id,
        step_id="retry-verification",
        decision="APPROVE",
        actor_id="test-local-operator",
    )
    assert engine.human_intervention_queue.mark_verifying(request_id)

    recovered = isolated_engine(tmp_path)
    recovered._load_missions()
    assert recovered.human_intervention_queue.get_request(request_id)["status"] == "RESPONSE_RECEIVED"
    assert recovered.active_missions[mission.mission_id].status == MissionStatus.WAITING_FOR_USER
