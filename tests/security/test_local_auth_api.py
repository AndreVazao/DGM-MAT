# Path: C:\\ProgramasGodMode\\DGM-MAT\\tests\\security\\test_local_auth_api.py
from pathlib import Path

from fastapi.testclient import TestClient

from core.api.api_server import app
from core.api import local_auth_api


def _configure_bootstrap(monkeypatch, tmp_path: Path):
    secret = "test-bootstrap-secret-" + ("x" * 64)
    secret_file = tmp_path / "bootstrap.token"
    secret_file.write_text(secret, encoding="utf-8")
    monkeypatch.setattr(local_auth_api, "_bootstrap_path", lambda: secret_file)
    # TestClient uses a synthetic peer name; loopback policy is tested separately.
    monkeypatch.setattr(local_auth_api, "_is_loopback", lambda request: True)
    with local_auth_api._lock:
        local_auth_api._attempts.clear()
    local_auth_api.session_manager.revoke_all()
    return secret


def test_bootstrap_exchange_issues_scoped_session(monkeypatch, tmp_path):
    secret = _configure_bootstrap(monkeypatch, tmp_path)
    with TestClient(app, base_url="http://127.0.0.1:8181") as client:
        response = client.post(
            "/auth/session",
            headers={"Authorization": f"Bearer {secret}"},
            json={"client_id": "desktop-test"},
        )
    assert response.status_code == 201
    payload = response.json()
    assert payload["token_type"] == "Bearer"
    assert payload["expires_in"] == 1800
    assert set(payload["scopes"]) == {"local-client", "operator"}
    assert local_auth_api.session_manager.authenticate(
        payload["access_token"], required_scope="operator"
    ) is not None


def test_missing_or_invalid_bootstrap_is_rejected(monkeypatch, tmp_path):
    secret = _configure_bootstrap(monkeypatch, tmp_path)
    with TestClient(app, base_url="http://127.0.0.1:8181") as client:
        missing = client.post("/auth/session", json={"client_id": "desktop-test"})
        invalid = client.post(
            "/auth/session",
            headers={"Authorization": "Bearer wrong-secret"},
            json={"client_id": "desktop-test"},
        )
    assert missing.status_code == 401
    assert invalid.status_code == 401
    assert secret not in missing.text + invalid.text


def test_untrusted_origin_is_rejected(monkeypatch, tmp_path):
    secret = _configure_bootstrap(monkeypatch, tmp_path)
    with TestClient(app, base_url="http://127.0.0.1:8181") as client:
        response = client.post(
            "/auth/session",
            headers={
                "Authorization": f"Bearer {secret}",
                "Origin": "https://evil.example",
            },
            json={"client_id": "desktop-test"},
        )
    assert response.status_code == 403


def test_invalid_client_payload_is_rejected(monkeypatch, tmp_path):
    secret = _configure_bootstrap(monkeypatch, tmp_path)
    with TestClient(app, base_url="http://127.0.0.1:8181") as client:
        response = client.post(
            "/auth/session",
            headers={"Authorization": f"Bearer {secret}"},
            json={"client_id": "desktop-test", "scopes": ["operator", "admin"]},
        )
    assert response.status_code == 422


def test_missing_bootstrap_file_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setattr(local_auth_api, "_bootstrap_path", lambda: tmp_path / "missing.token")
    monkeypatch.setattr(local_auth_api, "_is_loopback", lambda request: True)
    with TestClient(app, base_url="http://127.0.0.1:8181") as client:
        response = client.post("/auth/session", json={"client_id": "desktop-test"})
    assert response.status_code == 503
