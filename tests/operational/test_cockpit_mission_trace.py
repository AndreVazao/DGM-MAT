import pytest
from fastapi.testclient import TestClient
from core.api.api_server import app
from core.runtime.runtime_state_store import state_store
from core.autonomy.mission_engine import mission_engine
from core.runtime.safe_action_queue import SafeActionQueue

client = TestClient(app)

def test_cockpit_mission_trace():
    # 1. Simulate Cockpit sending a directive
    directive = "list repositories in workspace"
    response = client.post("/runtime/missions", json={"goal": directive})
    assert response.status_code == 200
    data = response.json()
    mission_id = data["mission_id"]
    assert mission_id is not None

    # 2. Verify Mission was created in Truth State
    truth = state_store.get_snapshot()
    assert mission_id in truth.missions
    assert truth.missions[mission_id]["goal"] == directive

    # 3. Verify Action was enqueued in SafeActionQueue
    queue = SafeActionQueue()
    queued_actions = queue.list_queued()
    # Find the action for this mission
    action = next((a for a in queued_actions if a["payload"].get("mission_id") == mission_id), None)
    assert action is not None
    assert action["action_type"] == "MISSION_EXECUTION"

def test_failed_mission_trace():
    # 1. Simulate invalid directive
    directive = "x" # too short
    response = client.post("/runtime/missions", json={"goal": directive})
    assert response.status_code == 200 # API succeeds but mission fails internally
    data = response.json()
    mission_id = data["mission_id"]

    # 2. Verify Mission marked as FAILED in Truth State
    truth = state_store.get_snapshot()
    assert mission_id in truth.missions
    assert truth.missions[mission_id]["status"] == "failed"
