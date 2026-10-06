from datetime import datetime
from core.autonomy.mission_models import Mission, MissionStatus
from core.contracts.compat import action_payload_to_execution_request, approval_to_contract, decision_to_contract, event_to_contract, mission_to_contract
from shared.models.event import Event

def test_action_payload_adapter():
    contract = action_payload_to_execution_request({"mission_id": "mission_123", "goal": "test"})
    assert contract.mission_id == "mission_123"
    assert contract.arguments["goal"] == "test"

def test_approval_and_decision_adapters():
    approval = approval_to_contract("task_1", {"status": "awaiting_approval", "diff": "x", "impact": "HIGH"})
    decision = decision_to_contract(approval.approval_id, "approved", decided_by="andre")
    assert approval.status == "PENDING"
    assert decision.decision == "APPROVED"

def test_event_adapter():
    event = Event(source="test", target="core", event_type="TEST", payload={"x": 1})
    contract = event_to_contract(event)
    assert contract.event_id == event.id
    assert contract.payload == {"x": 1}

def test_mission_adapter():
    now = datetime.now()
    mission = Mission("mission_1", "goal", "description", status=MissionStatus.QUEUED, created_at=now, updated_at=now)
    contract = mission_to_contract(mission)
    assert contract.mission_id == "mission_1"
    assert contract.status == "QUEUED"
