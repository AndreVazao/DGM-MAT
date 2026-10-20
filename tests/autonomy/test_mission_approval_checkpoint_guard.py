from core.autonomy.mission_engine import MissionEngine
from core.autonomy.mission_models import Mission, MissionStatus


class _FakeApprovalManager:
    def __init__(self, request_id):
        self.approvals = {request_id: {"status": "awaiting_approval"}}
        self.decisions = []

    def approve(self, request_id):
        self.decisions.append((request_id, "approve"))

    def reject(self, request_id):
        self.decisions.append((request_id, "reject"))


def _mission(mission_id, request_id, status):
    return Mission(
        mission_id=mission_id,
        goal="Approval checkpoint regression",
        description="test only",
        status=status,
        metadata={"approval_request_id": request_id},
    )


def test_late_approval_does_not_overwrite_terminal_durable_mission(tmp_path, monkeypatch):
    engine = MissionEngine()
    engine.missions_path = tmp_path
    monkeypatch.setattr(engine, "_sync_state", lambda mission: None)
    request_id = "approval-terminal-regression"
    durable = _mission("mission-terminal-approval", request_id, MissionStatus.COMPLETED)
    engine.save_mission(durable)

    # Simulate a second process with an obsolete in-memory status.
    stale = _mission(durable.mission_id, request_id, MissionStatus.APPROVAL_PENDING)
    engine.active_missions = {stale.mission_id: stale}
    approvals = _FakeApprovalManager(request_id)
    engine.approval_manager = approvals

    assert engine.handle_approval_decision(request_id, "approve") is False
    assert stale.status is MissionStatus.COMPLETED
    assert "last_decision" not in stale.metadata
    assert approvals.decisions == []

    persisted = engine._mission_from_checkpoint_data(
        __import__("json").loads((tmp_path / f"{durable.mission_id}.json").read_text(encoding="utf-8"))
    )
    assert persisted.status is MissionStatus.COMPLETED
    assert "last_decision" not in persisted.metadata


def test_approval_refreshes_and_preserves_nonterminal_durable_mission(tmp_path, monkeypatch):
    engine = MissionEngine()
    engine.missions_path = tmp_path
    monkeypatch.setattr(engine, "_sync_state", lambda mission: None)
    request_id = "approval-active-regression"
    durable = _mission("mission-active-approval", request_id, MissionStatus.APPROVAL_PENDING)
    engine.save_mission(durable)

    stale = _mission(durable.mission_id, request_id, MissionStatus.QUEUED)
    engine.active_missions = {stale.mission_id: stale}
    approvals = _FakeApprovalManager(request_id)
    engine.approval_manager = approvals

    assert engine.handle_approval_decision(request_id, "approve") is True
    assert stale.status is MissionStatus.APPROVAL_PENDING
    assert stale.metadata["last_decision"] == "approve"
    assert approvals.decisions == [(request_id, "approve")]

    persisted = __import__("json").loads(
        (tmp_path / f"{durable.mission_id}.json").read_text(encoding="utf-8")
    )
    assert persisted["status"] == MissionStatus.APPROVAL_PENDING.value
    assert persisted["metadata"]["last_decision"] == "approve"


def test_invalid_approval_decision_does_not_mutate_durable_approval(tmp_path, monkeypatch):
    engine = MissionEngine()
    engine.missions_path = tmp_path
    monkeypatch.setattr(engine, "_sync_state", lambda mission: None)
    request_id = "approval-invalid-regression"
    approvals = _FakeApprovalManager(request_id)
    engine.approval_manager = approvals

    assert engine.handle_approval_decision(request_id, "maybe") is False
    assert approvals.decisions == []
