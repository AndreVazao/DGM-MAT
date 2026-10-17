from datetime import datetime, timedelta

from core.autonomy.mission_engine import MissionEngine
from core.autonomy.mission_models import Mission, MissionStatus


def _stale_mission(engine, mission_id, action_id, now):
    old = now - timedelta(minutes=5)
    mission = Mission(
        mission_id=mission_id,
        goal="Recovery regression test",
        description="test only",
        status=MissionStatus.RUNNING,
        metadata={"action_id": action_id, "execution_started_at": old.isoformat()},
        created_at=old,
        updated_at=old,
    )
    engine.active_missions[mission_id] = mission
    engine.save_mission(mission)
    return mission


def test_stale_running_mission_with_unapproved_action_returns_to_queue(tmp_path):
    engine = MissionEngine()
    engine.missions_path = tmp_path
    engine.active_missions = {}
    now = datetime.now()
    mission_id = "recovery-unapproved-test"
    action_id = engine.action_queue.enqueue("MISSION_EXECUTION", {"mission_id": mission_id, "goal": "Recovery regression test"})
    mission = _stale_mission(engine, mission_id, action_id, now)

    report = engine.recover_interrupted_missions(now=now)

    assert report["requeued_unapproved"] == 1
    assert mission.status is MissionStatus.QUEUED
    assert mission.metadata["recovery"]["automatic_replay"] is False
    assert engine.action_queue.get_action(action_id)["status"] == "QUEUED"
    assert engine.action_queue.get_action(action_id)["is_approved"] is False


def test_stale_running_mission_with_explicitly_approved_action_is_not_rewritten(tmp_path):
    engine = MissionEngine()
    engine.missions_path = tmp_path
    engine.active_missions = {}
    now = datetime.now()
    mission_id = "recovery-approved-test"
    action_id = engine.action_queue.enqueue("MISSION_EXECUTION", {"mission_id": mission_id, "goal": "Recovery regression test"})
    engine.action_queue.approve(action_id, operator="recovery-regression-test")
    mission = _stale_mission(engine, mission_id, action_id, now)

    report = engine.recover_interrupted_missions(now=now)

    assert report["awaiting_approved_action"] == 1
    assert mission.status is MissionStatus.RUNNING
    assert engine.action_queue.get_action(action_id)["status"] == "APPROVED"
    assert engine.action_queue.get_action(action_id)["is_approved"] is True


def test_queued_and_approval_pending_missions_do_not_timeout_from_creation_time(tmp_path, monkeypatch):
    import pytest

    engine = MissionEngine()
    engine.missions_path = tmp_path
    engine.active_missions = {}
    old = datetime.now() - timedelta(minutes=10)

    for status in (MissionStatus.QUEUED, MissionStatus.APPROVAL_PENDING):
        mission_id = f"waiting-{status.value.lower()}-timeout-regression"
        mission = Mission(
            mission_id=mission_id,
            goal="Waiting mission timeout regression",
            description="Must wait for worker or approval without timing out",
            status=status,
            created_at=old,
            updated_at=old,
        )
        engine.active_missions[mission_id] = mission

    monkeypatch.setattr(
        engine,
        "_timeout_mission",
        lambda mission, reason: pytest.fail(f"waiting mission timed out: {mission.mission_id}"),
    )

    engine.process_missions()

    assert engine.active_missions["waiting-queued-timeout-regression"].status is MissionStatus.QUEUED
    assert engine.active_missions["waiting-approval_pending-timeout-regression"].status is MissionStatus.APPROVAL_PENDING

def test_queue_execution_starts_execution_clock_for_non_repository_mission(tmp_path, monkeypatch):
    engine = MissionEngine()
    engine.missions_path = tmp_path
    engine.active_missions = {}
    created_at = datetime.now() - timedelta(days=3)
    mission = Mission(
        mission_id="approved-old-mission-start-clock-regression",
        goal="Build a small local feature",
        description="Test execution start clock after approval",
        status=MissionStatus.QUEUED,
        created_at=created_at,
        updated_at=created_at,
    )
    engine.active_missions[mission.mission_id] = mission

    def observe_decomposition(mission_id):
        assert mission_id == mission.mission_id
        assert mission.metadata.get("execution_started_at")
        assert mission.status is MissionStatus.RUNNING
        return []

    monkeypatch.setattr(engine, "decompose_mission", observe_decomposition)

    result = engine._handle_queue_execution({"mission_id": mission.mission_id})

    assert result["status"] == "decomposed"
    assert datetime.fromisoformat(mission.metadata["execution_started_at"]) > datetime.now() - timedelta(seconds=5)
    assert mission.metadata["execution_timeout_seconds"] == engine.MISSION_EXECUTION_TIMEOUT_SECONDS
