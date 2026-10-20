import pytest
from fastapi.testclient import TestClient
from core.api.api_server import app
from core.runtime.runtime_state_store import state_store
from core.autonomy.mission_engine import mission_engine
from core.autonomy.mission_models import Mission, MissionStatus
from core.runtime.safe_action_queue import SafeActionQueue
from core.api.local_auth_api import session_manager

client = TestClient(app)

def _headers():
    token, _ = session_manager.create_session("cockpit-trace-test", {"local-client", "operator"})
    return {"Authorization": f"Bearer {token}"}

def test_cockpit_mission_trace():
    # 1. Simulate Cockpit sending a directive
    directive = "list repositories in workspace"
    response = client.post("/runtime/missions", headers=_headers(), json={"goal": directive})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["mission_status"] == "QUEUED"
    assert data["action_id"] is not None
    assert data["action_status"] in {"QUEUED", "APPROVED"}
    mission_id = data["mission_id"]
    assert mission_id is not None

    # 2. Verify Mission was created in Truth State
    truth = state_store.get_snapshot()
    assert mission_id in truth.missions
    assert truth.missions[mission_id]["goal"] == directive
    assert truth.missions[mission_id]["status"] == "QUEUED"
    assert truth.missions[mission_id]["mission_id"] == mission_id

    # 3. Verify the durable action is correlated, whether waiting or safely auto-approved.
    queue = SafeActionQueue()
    action = queue.get_action(data["action_id"])
    assert action is not None
    assert action["payload"].get("mission_id") == mission_id
    assert action["action_type"] == "MISSION_EXECUTION"
    assert action["status"] in {"QUEUED", "APPROVED", "RUNNING", "COMPLETED"}

def test_failed_mission_trace():
    # 1. Invalid directives must be reported as failed, never as successful creation.
    directive = "x" # too short
    response = client.post("/runtime/missions", headers=_headers(), json={"goal": directive})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "failed"
    assert data["error"] == "Goal too short or invalid"
    mission_id = data["mission_id"]

    # 2. Verify Mission marked as FAILED in Truth State
    truth = state_store.get_snapshot()
    assert mission_id in truth.missions
    assert truth.missions[mission_id]["status"] == "FAILED"


def test_operator_can_approve_queue_action():
    response = client.post('/runtime/missions', headers=_headers(), json={'goal': 'summarize a test repository', 'description': 'approval API test'})
    assert response.status_code == 200
    mission_id = response.json()['mission_id']
    action_id = mission_engine.active_missions[mission_id].metadata['action_id']
    approved = client.post(f'/runtime/queue/actions/{action_id}/approve', headers=_headers())
    assert approved.status_code == 200
    assert approved.json()['status'] == 'approved'
    action = SafeActionQueue().get_action(action_id)
    assert action['status'] == 'APPROVED'
    assert action['is_approved'] is True
    assert action['approved_by'] == 'cockpit-trace-test'


def test_reject_queue_action_does_not_overwrite_durable_terminal_mission():
    response = client.post(
        "/runtime/missions",
        headers=_headers(),
        json={"goal": "summarize terminal mission test", "description": "terminal state regression"},
    )
    assert response.status_code == 200
    mission_id = response.json()["mission_id"]
    action_id = mission_engine.active_missions[mission_id].metadata["action_id"]
    cached = mission_engine.active_missions[mission_id]

    terminal_checkpoint = Mission(
        mission_id=mission_id,
        goal=cached.goal,
        description=cached.description,
        status=MissionStatus.COMPLETED,
        metadata=dict(cached.metadata),
        created_at=cached.created_at,
    )
    mission_engine.save_mission(terminal_checkpoint)

    rejected = client.post(
        f"/runtime/queue/actions/{action_id}/reject",
        headers=_headers(),
        json={"reason": "Test rejection must not overwrite completed mission"},
    )
    assert rejected.status_code == 200
    assert SafeActionQueue().get_action(action_id)["status"] == "REJECTED"
    assert mission_engine.active_missions[mission_id].status is MissionStatus.COMPLETED


def test_operator_can_reject_queue_action():
    response = client.post('/runtime/missions', headers=_headers(), json={'goal': 'summarize another test repository', 'description': 'rejection API test'})
    assert response.status_code == 200
    mission_id = response.json()['mission_id']
    action_id = mission_engine.active_missions[mission_id].metadata['action_id']
    rejected = client.post(f'/runtime/queue/actions/{action_id}/reject', headers=_headers(), json={'reason': 'Rejected by operator test'})
    assert rejected.status_code == 200
    assert rejected.json()['status'] == 'rejected'
    action = SafeActionQueue().get_action(action_id)
    assert action['status'] == 'REJECTED'
    assert action['error_message'] == 'Rejected by operator test'
    assert rejected.json()['mission_id'] == mission_id
    assert mission_engine.active_missions[mission_id].status.value == 'CANCELLED'
