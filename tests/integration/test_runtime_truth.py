import pytest
from fastapi.testclient import TestClient
from core.api.api_server import app
from core.runtime.runtime_state_store import state_store, StateEvents

client = TestClient(app)

def test_get_runtime_truth():
    # Dispatch a dummy state change to ensure state is initialized
    state_store.dispatch(StateEvents.COCKPIT_STATE_CHANGED, {"runtime_status": "test_running", "is_degraded": True})

    response = client.get("/runtime/truth")
    assert response.status_code == 200
    data = response.json()
    assert "runtime_status" in data
    assert data["runtime_status"] == "test_running"
    assert data["is_degraded"] == True
    assert "queue" in data
    assert "consumers" in data

def test_get_runtime_status_field_consistency():
    state_store.dispatch(StateEvents.COCKPIT_STATE_CHANGED, {"runtime_status": "running"})
    response = client.get("/runtime/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
