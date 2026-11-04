import pytest
from fastapi.testclient import TestClient
from core.api.api_server import app
from core.runtime.runtime_state_store import state_store, StateEvents
from core.api.local_auth_api import session_manager

client = TestClient(app)

def _headers():
    token, _ = session_manager.create_session("runtime-truth-test", {"local-client", "operator"})
    return {"Authorization": f"Bearer {token}"}

def test_get_runtime_truth():
    # Dispatch a dummy state change to ensure state is initialized
    state_store.dispatch(StateEvents.COCKPIT_STATE_CHANGED, {"runtime_status": "test_running", "is_degraded": True})

    response = client.get("/runtime/truth", headers=_headers())
    assert response.status_code == 200
    data = response.json()
    assert "runtime_status" in data
    assert data["runtime_status"] == "test_running"
    assert data["is_degraded"] == True
    assert "queue" in data
    assert "consumers" in data

def test_get_runtime_status_field_consistency():
    state_store.dispatch(StateEvents.COCKPIT_STATE_CHANGED, {"runtime_status": "running"})
    response = client.get("/runtime/status", headers=_headers())
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"


def test_active_mission_counters_exclude_queued_and_terminal_missions():
    previous = state_store.get_snapshot().missions.copy()
    fixtures = {
        "mission-running": {"id": "mission-running", "status": "RUNNING"},
        "mission-queued": {"id": "mission-queued", "status": "QUEUED"},
        "mission-failed": {"id": "mission-failed", "status": "FAILED"},
        "mission-completed": {"id": "mission-completed", "status": "COMPLETED"},
    }
    state_store.dispatch(StateEvents.MISSIONS_RECONCILED, fixtures)
    try:
        headers = _headers()
        status_response = client.get("/runtime/status", headers=headers)
        autonomy_response = client.get("/runtime/autonomy", headers=headers)

        assert status_response.status_code == 200
        assert autonomy_response.status_code == 200
        assert status_response.json()["missions_active"] == 1
        assert autonomy_response.json()["missions_active"] == 1
    finally:
        state_store.dispatch(StateEvents.MISSIONS_RECONCILED, previous)
