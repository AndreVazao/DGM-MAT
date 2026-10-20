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


class _FakeMissionActionQueue:
    def __init__(self, actions=None):
        self.actions = list(actions or [])
        self.next_id = 900

    def list_mission_execution_actions(self):
        return [dict(action) for action in self.actions]

    def enqueue(self, action_type, payload):
        self.next_id += 1
        action = {
            "id": self.next_id,
            "action_type": action_type,
            "payload": dict(payload),
            "status": "QUEUED",
            "is_approved": False,
        }
        self.actions.append(action)
        return action["id"]


def test_reconciliation_enqueues_missing_action_without_approval(tmp_path, monkeypatch):
    engine = MissionEngine()
    engine.missions_path = tmp_path
    engine.active_missions = {}
    monkeypatch.setattr(engine, "_sync_state", lambda mission: None)
    mission = Mission(
        mission_id="missing-queue-action",
        goal="Recover durable queue link",
        description="Crash between mission checkpoint and queue enqueue",
        status=MissionStatus.CREATED,
    )
    engine.active_missions[mission.mission_id] = mission
    queue = _FakeMissionActionQueue()
    engine.action_queue = queue

    report = engine._reconcile_mission_queue_links()

    assert report == {"linked_existing": 0, "enqueued_missing": 1, "conflicts": 0, "reconciled_rejections": 0}
    assert mission.status is MissionStatus.QUEUED
    assert mission.metadata["action_id"] == 901
    assert mission.metadata["queue_reconciliation"]["status"] == "MISSING_ACTION_CREATED_UNAPPROVED"
    assert queue.actions[0]["is_approved"] is False
    assert queue.actions[0]["status"] == "QUEUED"


def test_reconciliation_restores_existing_action_link_without_duplicate(tmp_path, monkeypatch):
    engine = MissionEngine()
    engine.missions_path = tmp_path
    engine.active_missions = {}
    monkeypatch.setattr(engine, "_sync_state", lambda mission: None)
    mission = Mission(
        mission_id="existing-queue-action",
        goal="Restore durable queue link",
        description="Crash after enqueue before checkpoint update",
        status=MissionStatus.CREATED,
        metadata={},
    )
    action = {
        "id": 321,
        "action_type": "MISSION_EXECUTION",
        "payload": {"mission_id": mission.mission_id, "goal": mission.goal},
        "status": "QUEUED",
        "is_approved": False,
    }
    queue = _FakeMissionActionQueue([action])
    engine.action_queue = queue
    engine.active_missions[mission.mission_id] = mission

    report = engine._reconcile_mission_queue_links()

    assert report == {"linked_existing": 1, "enqueued_missing": 0, "conflicts": 0, "reconciled_rejections": 0}
    assert mission.status is MissionStatus.QUEUED
    assert mission.metadata["action_id"] == 321
    assert len(queue.actions) == 1


def test_reconciliation_flags_duplicate_actions_without_choosing_or_approving(tmp_path, monkeypatch):
    engine = MissionEngine()
    engine.missions_path = tmp_path
    engine.active_missions = {}
    monkeypatch.setattr(engine, "_sync_state", lambda mission: None)
    mission = Mission(
        mission_id="duplicate-queue-actions",
        goal="Review duplicate durable actions",
        description="No automatic action selection",
        status=MissionStatus.QUEUED,
    )
    actions = [
        {"id": action_id, "action_type": "MISSION_EXECUTION",
         "payload": {"mission_id": mission.mission_id, "goal": mission.goal},
         "status": "QUEUED", "is_approved": False}
        for action_id in (41, 42)
    ]
    queue = _FakeMissionActionQueue(actions)
    engine.action_queue = queue
    engine.active_missions[mission.mission_id] = mission

    report = engine._reconcile_mission_queue_links()

    assert report == {"linked_existing": 0, "enqueued_missing": 0, "conflicts": 1, "reconciled_rejections": 0}
    assert mission.metadata["queue_reconciliation"]["status"] == "MULTIPLE_ACTIONS_REQUIRES_REVIEW"
    assert mission.metadata["queue_reconciliation"]["automatic_replay"] is False
    assert len(queue.actions) == 2
    assert all(not action["is_approved"] for action in queue.actions)


def test_reconciliation_cancels_mission_when_durable_queue_action_was_rejected(tmp_path, monkeypatch):
    engine = MissionEngine()
    engine.missions_path = tmp_path
    engine.active_missions = {}
    monkeypatch.setattr(engine, "_sync_state", lambda mission: None)
    mission = Mission(
        mission_id="rejected-action-crash-window",
        goal="Do not execute rejected work",
        description="Process may stop after queue rejection before mission save",
        status=MissionStatus.QUEUED,
        metadata={"action_id": 501},
    )
    action = {
        "id": 501,
        "action_type": "MISSION_EXECUTION",
        "payload": {"mission_id": mission.mission_id, "goal": mission.goal},
        "status": "REJECTED",
        "is_approved": False,
        "error_message": "Operator rejected this mission",
        "audit_trail": [{
            "status": "REJECTED",
            "operator": "reviewer-1",
            "reason": "Operator rejected this mission",
        }],
    }
    engine.action_queue = _FakeMissionActionQueue([action])
    engine.active_missions[mission.mission_id] = mission

    report = engine._reconcile_mission_queue_links()

    assert report == {"linked_existing": 0, "enqueued_missing": 0, "conflicts": 0, "reconciled_rejections": 1}
    assert mission.status is MissionStatus.CANCELLED
    assert mission.metadata["queue_rejection"]["reconciled_after_restart"] is True
    assert mission.metadata["queue_rejection"]["operator"] == "reviewer-1"
    assert mission.error == "Mission rejected by operator: Operator rejected this mission"
    assert engine.action_queue.actions[0]["status"] == "REJECTED"


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


def test_stale_running_mission_closes_interrupted_queue_action_without_replay(tmp_path):
    from core.storage.database import SessionLocal

    engine = MissionEngine()
    engine.missions_path = tmp_path
    engine.active_missions = {}
    now = datetime.now()
    mission_id = "recovery-running-action-test"
    action_id = engine.action_queue.enqueue(
        "MISSION_EXECUTION",
        {"mission_id": mission_id, "goal": "Recovery regression test"},
    )
    assert engine.action_queue.approve(action_id, operator="recovery-regression-test") is True

    # Simulate a worker that claimed the durable action and then crashed.
    with SessionLocal() as session:
        assert engine.action_queue._claim_approved_action(session, action_id) is True

    mission = _stale_mission(engine, mission_id, action_id, now)
    report = engine.recover_interrupted_missions(now=now)

    action = engine.action_queue.get_action(action_id)
    assert report["failed_requires_review"] == 1
    assert mission.status is MissionStatus.FAILED
    assert mission.metadata["recovery"]["automatic_replay"] is False
    assert mission.metadata["recovery"]["queue_action_reconciliation"] == "FAILED_REQUIRES_REVIEW"
    assert mission.metadata["recovery"]["action_status"] == "FAILED"
    assert action["status"] == "FAILED"
    assert "automatic replay is disabled" in action["error_message"]
    assert any(
        entry.get("event") == "INTERRUPTED_ACTION_RECONCILED"
        and entry.get("automatic_replay") is False
        for entry in action["audit_trail"]
    )


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

def test_queue_handler_refreshes_terminal_checkpoint_before_execution(tmp_path, monkeypatch):
    import pytest

    engine = MissionEngine()
    engine.missions_path = tmp_path
    monkeypatch.setattr(engine, "_sync_state", lambda mission: None)
    mission_id = "terminal-checkpoint-execution-guard"
    persisted = Mission(
        mission_id=mission_id,
        goal="Do not resurrect a terminal mission",
        description="Persisted terminal state must win over stale memory",
        status=MissionStatus.CANCELLED,
    )
    engine.save_mission(persisted)

    # Simulate another process holding an old RUNNING snapshot.
    stale = Mission(
        mission_id=mission_id,
        goal=persisted.goal,
        description=persisted.description,
        status=MissionStatus.RUNNING,
    )
    engine.active_missions[mission_id] = stale

    with pytest.raises(ValueError, match=r"is terminal \(CANCELLED\)"):
        engine._handle_queue_execution({"mission_id": mission_id})

    assert engine.active_missions[mission_id].status is MissionStatus.CANCELLED
    assert stale.status is MissionStatus.CANCELLED


def test_queue_handler_refuses_missing_checkpoint_instead_of_using_stale_cache(tmp_path, monkeypatch):
    import pytest

    engine = MissionEngine()
    engine.missions_path = tmp_path
    monkeypatch.setattr(engine, "_sync_state", lambda mission: None)
    stale = Mission(
        mission_id="missing-durable-checkpoint",
        goal="Do not use stale cache",
        description="Checkpoint was removed or unavailable",
        status=MissionStatus.QUEUED,
    )
    engine.active_missions[stale.mission_id] = stale

    with pytest.raises(ValueError, match="checkpoint unavailable"):
        engine._handle_queue_execution({"mission_id": stale.mission_id})

    assert stale.mission_id not in engine.active_missions


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
    engine.save_mission(mission)

    def observe_decomposition(mission_id):
        assert mission_id == mission.mission_id
        assert mission.metadata.get("execution_started_at")
        assert mission.status is MissionStatus.RUNNING
        return []

    monkeypatch.setattr(engine, "decompose_mission", observe_decomposition)

    result = engine._handle_queue_execution({"mission_id": mission.mission_id})

    # Planning-only is not execution: without a generic executor the mission
    # must terminate truthfully as failed rather than report "decomposed" as success.
    assert result["status"] == "failed"
    assert mission.status is MissionStatus.FAILED
    assert datetime.fromisoformat(mission.metadata["execution_started_at"]) > datetime.now() - timedelta(seconds=5)
    assert mission.metadata["execution_timeout_seconds"] == engine.MISSION_EXECUTION_TIMEOUT_SECONDS
