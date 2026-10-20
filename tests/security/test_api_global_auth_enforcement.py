from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from core.api.api_server import app
from core.api.local_auth_api import session_manager
from core.operations.command_executor import CommandExecutor


@pytest.fixture
def client():
    session_manager.revoke_all()
    with TestClient(app, base_url="http://127.0.0.1:8181") as value:
        yield value
    session_manager.revoke_all()


def _session(scopes=None):
    return session_manager.create_session(
        "security-test-client",
        scopes or {"local-client", "operator"},
    )[0]


def test_health_is_the_only_public_http_route(client):
    assert client.get("/health").status_code == 200
    response = client.get("/runtime/truth")
    assert response.status_code == 401
    assert "access_token" not in response.text


def test_valid_session_allows_local_read_and_operator_action_route(client):
    token = _session()
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/runtime/truth", headers=headers).status_code == 200
    response = client.post("/runtime/missions", headers=headers, json={})
    assert response.status_code == 422


def test_blank_or_whitespace_mission_goal_is_rejected(client):
    token = _session()
    headers = {"Authorization": f"Bearer {token}"}

    for goal in ("", "   "):
        response = client.post(
            "/runtime/missions",
            headers=headers,
            json={"goal": goal, "description": "must not create"},
        )
        assert response.status_code == 422


def test_expired_or_revoked_session_is_rejected(client):
    token = _session()
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/runtime/truth", headers=headers).status_code == 200
    assert session_manager.revoke(token)
    assert client.get("/runtime/truth", headers=headers).status_code == 401


def test_insufficient_scope_is_rejected(client):
    token = _session({"local-client"})
    response = client.post(
        "/runtime/missions",
        headers={"Authorization": f"Bearer {token}"},
        json={"goal": "test", "description": "must not create"},
    )
    assert response.status_code in {400, 403}


def test_governed_command_routes_require_operator_session(client):
    assert client.get("/governance/commands/catalog").status_code == 401
    assert client.post(
        "/governance/commands/run",
        json={"command_id": "system.summary"},
    ).status_code == 401

    read_only_token = _session({"local-client"})
    read_only_headers = {"Authorization": f"Bearer {read_only_token}"}
    assert client.get(
        "/governance/commands/catalog", headers=read_only_headers
    ).status_code == 403
    assert client.post(
        "/governance/commands/run",
        headers=read_only_headers,
        json={"command_id": "not-allowed"},
    ).status_code == 403


def test_operator_session_can_read_catalog_and_invalid_command_is_denied(client, tmp_path, monkeypatch):
    monkeypatch.setenv("DGM_COMMAND_AUDIT_PATH", str(tmp_path / "audit.jsonl"))
    token = _session()
    headers = {"Authorization": f"Bearer {token}"}
    catalog = client.get("/governance/commands/catalog", headers=headers)
    assert catalog.status_code == 200
    assert catalog.json()["arbitrary_shell"] is False

    response = client.post(
        "/governance/commands/run",
        headers=headers,
        json={"command_id": "powershell.raw", "target_path": "C:/"},
    )
    assert response.status_code == 400
    audit_lines = (tmp_path / "audit.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(audit_lines) == 2


def test_command_is_not_run_when_audit_storage_is_unavailable(client, tmp_path, monkeypatch):
    blocker = tmp_path / "blocker"
    blocker.write_text("file blocks directory", encoding="utf-8")
    monkeypatch.setenv("DGM_COMMAND_AUDIT_PATH", str(blocker / "audit.jsonl"))
    monkeypatch.setattr(
        CommandExecutor,
        "execute",
        lambda *args, **kwargs: pytest.fail("executor must not run without a persisted request audit"),
    )
    token = _session()
    response = client.post(
        "/governance/commands/run",
        headers={"Authorization": f"Bearer {token}"},
        json={"command_id": "system.summary"},
    )
    assert response.status_code == 503
    assert "execution refused" in response.text


def test_websocket_requires_session_header(client):
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("/ws"):
            pass
    assert exc.value.code == 1008


def test_authenticated_websocket_accepts_session_header(client):
    token = _session()
    with client.websocket_connect(
        "/ws",
        headers={"Authorization": f"Bearer {token}"},
    ) as websocket:
        websocket.close()


def test_cors_is_not_wildcard_and_rejects_untrusted_preflight(client):
    response = client.options(
        "/runtime/truth",
        headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code in {400, 403}

def test_queue_decision_routes_require_operator_session(client):
    assert client.post("/runtime/queue/actions/999999/approve").status_code == 401
    assert client.post(
        "/runtime/queue/actions/999999/reject",
        json={"reason": "reject for security test"},
    ).status_code == 401

    read_only_token = _session({"local-client"})
    headers = {"Authorization": f"Bearer {read_only_token}"}
    assert client.post(
        "/runtime/queue/actions/999999/approve", headers=headers
    ).status_code == 403
    assert client.post(
        "/runtime/queue/actions/999999/reject",
        headers=headers,
        json={"reason": "reject for security test"},
    ).status_code == 403



def test_office_telemetry_requires_operator_session(client):
    assert client.get("/runtime/office/telemetry").status_code == 401

    read_only_token = _session({"local-client"})
    assert client.get(
        "/runtime/office/telemetry",
        headers={"Authorization": f"Bearer {read_only_token}"},
    ).status_code == 403
