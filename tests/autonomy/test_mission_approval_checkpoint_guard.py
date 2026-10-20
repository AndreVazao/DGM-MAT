from core.autonomy.mission_engine import MissionEngine
from core.autonomy.mission_models import Mission, MissionStatus


class _FakeApprovalManager:
    def __init__(self, request_id):
        self.approvals = {request_id: {"status": "awaiting_approval"}}
        self.decisions = []

    def approve(self, request_id):
        self.decisions.append((request_id, "approve"))
        return True

    def reject(self, request_id):
        self.decisions.append((request_id, "reject"))
        return True


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


def test_legacy_rejection_cancels_mission_instead_of_marking_execution_failed(tmp_path, monkeypatch):
    engine = MissionEngine()
    engine.missions_path = tmp_path
    monkeypatch.setattr(engine, "_sync_state", lambda mission: None)
    request_id = "approval-rejection-cancel-regression"
    mission = _mission(
        "mission-rejected-by-user",
        request_id,
        MissionStatus.APPROVAL_PENDING,
    )
    mission.metadata["last_decision"] = "reject"
    engine.save_mission(mission)
    engine.active_missions = {mission.mission_id: mission}
    engine.approval_manager = _FakeApprovalManager(request_id)

    engine._handle_approval_pending(mission)

    assert mission.status is MissionStatus.CANCELLED
    assert mission.error == "User rejected mission."
    persisted = __import__("json").loads(
        (tmp_path / f"{mission.mission_id}.json").read_text(encoding="utf-8")
    )
    assert persisted["status"] == MissionStatus.CANCELLED.value
    assert persisted["error"] == "User rejected mission."


def test_rejected_durable_transition_does_not_mutate_mission_checkpoint(tmp_path, monkeypatch):
    engine = MissionEngine()
    engine.missions_path = tmp_path
    monkeypatch.setattr(engine, "_sync_state", lambda mission: None)
    request_id = "approval-rejection-race-regression"
    mission = _mission(
        "mission-rejection-race",
        request_id,
        MissionStatus.APPROVAL_PENDING,
    )
    engine.save_mission(mission)
    engine.active_missions = {mission.mission_id: mission}

    class _DecisionRaceManager(_FakeApprovalManager):
        def reject(self, request_id):
            self.decisions.append((request_id, "reject"))
            return False

    approvals = _DecisionRaceManager(request_id)
    engine.approval_manager = approvals

    assert engine.handle_approval_decision(request_id, "reject") is False
    assert mission.status is MissionStatus.APPROVAL_PENDING
    assert "last_decision" not in mission.metadata
    assert approvals.decisions == [(request_id, "reject")]

    persisted = __import__("json").loads(
        (tmp_path / f"{mission.mission_id}.json").read_text(encoding="utf-8")
    )
    assert persisted["status"] == MissionStatus.APPROVAL_PENDING.value
    assert "last_decision" not in persisted["metadata"]


def test_rejected_alias_is_stored_as_canonical_legacy_decision(tmp_path, monkeypatch):
    engine = MissionEngine()
    engine.missions_path = tmp_path
    monkeypatch.setattr(engine, "_sync_state", lambda mission: None)
    request_id = "approval-rejected-alias"
    mission = _mission(
        "mission-rejected-alias",
        request_id,
        MissionStatus.APPROVAL_PENDING,
    )
    engine.save_mission(mission)
    engine.active_missions = {mission.mission_id: mission}
    approvals = _FakeApprovalManager(request_id)
    engine.approval_manager = approvals

    assert engine.handle_approval_decision(request_id, "rejected") is True
    assert mission.metadata["last_decision"] == "reject"
    assert approvals.decisions == [(request_id, "reject")]


def test_approval_action_id_is_recovered_from_legacy_id_field(tmp_path, monkeypatch):
    engine = MissionEngine()
    engine.missions_path = tmp_path
    monkeypatch.setattr(engine, "_sync_state", lambda mission: None)
    mission = _mission("mission-approval-link", "unused", MissionStatus.APPROVAL_PENDING)
    engine.active_missions = {mission.mission_id: mission}

    class _ApprovalWithLegacyId:
        def request_approval(self, request_id, description, risk_score, impact):
            return {"id": 73}

    engine.approval_manager = _ApprovalWithLegacyId()

    request_id = engine.request_approval(mission.mission_id, "Needs approval")
    assert request_id == mission.metadata["approval_request_id"]
    assert mission.metadata["approval_action_id"] == 73


def test_legacy_scheduler_recovers_durable_rejection_after_checkpoint_gap(tmp_path, monkeypatch):
    engine = MissionEngine()
    engine.missions_path = tmp_path
    monkeypatch.setattr(engine, "_sync_state", lambda mission: None)
    request_id = "approval-rejection-recovery"
    mission = _mission(
        "mission-rejection-recovery",
        request_id,
        MissionStatus.APPROVAL_PENDING,
    )
    engine.save_mission(mission)
    engine.active_missions = {mission.mission_id: mission}
    approvals = _FakeApprovalManager(request_id)
    approvals.approvals[request_id]["status"] = "rejected"
    engine.approval_manager = approvals

    # Simulate a crash after the durable approval record was rejected but before
    # last_decision was written to the mission checkpoint.
    engine._handle_approval_pending(mission)

    assert mission.status is MissionStatus.CANCELLED
    assert mission.error == "User rejected mission."
    persisted = __import__("json").loads(
        (tmp_path / f"{mission.mission_id}.json").read_text(encoding="utf-8")
    )
    assert persisted["status"] == MissionStatus.CANCELLED.value
