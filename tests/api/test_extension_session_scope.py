from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.api import browser_capture_api, local_auth_api
from core.api.auth_middleware import LocalSessionAuthMiddleware
from core.recovery.recovery_ledger import RecoveryLedger


def test_extension_session_is_limited_to_browser_capture_routes(monkeypatch, tmp_path):
    ledger = RecoveryLedger(tmp_path / "ledger.sqlite3")
    monkeypatch.setattr(browser_capture_api, "_ledger", lambda: ledger)

    app = FastAPI()
    app.include_router(browser_capture_api.router)

    @app.get("/recovery/status")
    def operator_only_status():
        return {"status": "operator"}

    app.add_middleware(
        LocalSessionAuthMiddleware,
        routes=app.router.routes,
        session_manager=local_auth_api.session_manager,
        additional_session_managers=(local_auth_api.extension_session_manager,),
    )
    client = TestClient(app)
    extension_token, extension_principal = local_auth_api.extension_session_manager.create_session(
        "dgm-mat-chrome-extension", {"browser-capture"}
    )
    operator_token, operator_principal = local_auth_api.session_manager.create_session(
        "test-operator", {"operator"}
    )

    assert extension_principal.expires_at - extension_principal.issued_at == 8 * 60 * 60
    assert client.get(
        "/recovery/browser-capture/status",
        headers={"Authorization": "Bearer " + extension_token},
    ).status_code == 200
    assert client.get(
        "/recovery/status",
        headers={"Authorization": "Bearer " + extension_token},
    ).status_code == 403
    assert client.get(
        "/recovery/browser-capture/status",
        headers={"Authorization": "Bearer " + operator_token},
    ).status_code == 200
    assert client.get(
        "/recovery/status",
        headers={"Authorization": "Bearer " + operator_token},
    ).status_code == 200
