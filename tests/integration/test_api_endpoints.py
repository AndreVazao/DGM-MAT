import pytest
from fastapi.testclient import TestClient
from core.api.api_server import app
from core.api.local_auth_api import session_manager

client = TestClient(app)

def _headers():
    token, _ = session_manager.create_session("integration-test", {"local-client", "operator"})
    return {"Authorization": f"Bearer {token}"}

def test_repo_scan_endpoint():
    response = client.get("/runtime/repo_scan", headers=_headers())
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "files_scanned" in data

def test_memory_stats_endpoint():
    response = client.get("/runtime/memory/stats", headers=_headers())
    assert response.status_code == 200
    data = response.json()
    assert "total_memories" in data
