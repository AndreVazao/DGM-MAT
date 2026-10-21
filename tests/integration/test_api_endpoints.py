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


def test_mission_detail_endpoint_reads_one_durable_checkpoint(monkeypatch, tmp_path):
    import json
    from core.api import runtime_api

    mission_id = "mission_abcdef12"
    checkpoint = {
        "mission_id": mission_id,
        "status": "COMPLETED",
        "progress": 1.0,
        "created_at": "2026-10-21T10:00:00",
        "updated_at": "2026-10-21T10:01:00",
        "metadata": {
            "result": {"handler": "read_only_diagnostic", "summary": "Validation complete"},
            "output": "Observed result",
        },
    }
    (tmp_path / f"{mission_id}.json").write_text(json.dumps(checkpoint), encoding="utf-8")
    monkeypatch.setattr(runtime_api.mission_engine, "missions_path", tmp_path)

    response = client.get(f"/runtime/missions/{mission_id}", headers=_headers())

    assert response.status_code == 200
    data = response.json()
    assert data["mission_id"] == mission_id
    assert data["status"] == "COMPLETED"
    assert data["result"]["summary"] == "Validation complete"
    assert data["output"] == "Observed result"
    assert data["source"] == "durable_mission_checkpoint"


def test_mission_detail_endpoint_does_not_accept_path_like_ids():
    response = client.get("/runtime/missions/../../secrets", headers=_headers())
    assert response.status_code == 404


def test_mission_detail_endpoint_returns_404_for_missing_checkpoint(monkeypatch, tmp_path):
    from core.api import runtime_api

    monkeypatch.setattr(runtime_api.mission_engine, "missions_path", tmp_path)
    response = client.get("/runtime/missions/mission_deadbeef", headers=_headers())
    assert response.status_code == 404
