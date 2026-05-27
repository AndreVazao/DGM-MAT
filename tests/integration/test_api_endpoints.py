import pytest
from fastapi.testclient import TestClient
from core.api.api_server import app

client = TestClient(app)

def test_repo_scan_endpoint():
    response = client.get("/runtime/repo_scan")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "files_scanned" in data

def test_memory_stats_endpoint():
    response = client.get("/runtime/memory/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_memories" in data
