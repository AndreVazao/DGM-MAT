# Path: C:\\ProgramasGodMode\\DGM-MAT\\tests\\security\\test_api_global_auth_enforcement.py
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from core.api.api_server import app
from core.api.local_auth_api import session_manager


@pytest.fixture
def client():
    session_manager.revoke_all()
    with TestClient(app, base_url="http://127.0.0.1:8181") as value:
        yield value
    session_manager.revoke_all()


def _session():
    return session_manager.create_session(
        "security-test-client",
        {"local-client", "operator"},
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
    # This route is only invoked with a deliberately invalid payload; auth must pass first.
    response = client.post("/runtime/missions", headers=headers, json={})
    assert response.status_code == 422


def test_expired_or_revoked_session_is_rejected(client):
    token = _session()
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/runtime/truth", headers=headers).status_code == 200
    assert session_manager.revoke(token)
    assert client.get("/runtime/truth", headers=headers).status_code == 401


def test_insufficient_scope_is_rejected(client):
    token = session_manager.create_session("read-only", {"local-client"})[0]
    response = client.post(
        "/runtime/missions",
        headers={"Authorization": f"Bearer {token}"},
        json={"goal": "test", "description": "must not create"},
    )
    assert response.status_code in {400, 403}


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
