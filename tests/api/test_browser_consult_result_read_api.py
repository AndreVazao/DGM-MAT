from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from core.api import browser_consult_api
from core.api.security_policy import SecurityScope, classify_request_path
from core.recovery.browser_consult_store import BrowserConsultStore


def _client(monkeypatch, tmp_path):
    monkeypatch.setenv("DGM_BROWSER_CONSULT_ENABLED", "1")
    monkeypatch.setenv("DGM_BROWSER_CONSULT_FREE_PROVIDERS", "chatgpt")
    store = BrowserConsultStore(tmp_path / "consult.sqlite3")
    monkeypatch.setattr(browser_consult_api, "_store", lambda: store)
    monkeypatch.setattr(browser_consult_api, "_audit", lambda *args, **kwargs: None)
    app = FastAPI()

    @app.middleware("http")
    async def local_principal(request: Request, call_next):
        request.scope.setdefault("state", {})["dgm_principal"] = {
            "subject": "test-operator",
            "session_id": "test-session",
            "scopes": ["operator"],
        }
        return await call_next(request)

    app.include_router(browser_consult_api.router)
    return TestClient(app), store


def test_result_endpoint_returns_completed_untrusted_receipt(monkeypatch, tmp_path):
    client, store = _client(monkeypatch, tmp_path)
    queued = client.post("/recovery/browser-consult/enqueue", json={
        "task_ref": "mission_1234abcd",
        "goal": "Review the mission dispatch boundary",
        "providers": ["chatgpt"],
        "free_capacity_confirmed": True,
    })
    consultation_id = queued.json()["consultation_ids"][0]
    assert client.post("/recovery/browser-consult/approve/" + consultation_id).status_code == 200
    claimed = client.post("/recovery/browser-consult/next?provider=chatgpt", json={}).json()["next"]
    finished = client.post("/recovery/browser-consult/result", json={
        "consultation_id": consultation_id,
        "claim_token": claimed["claim_token"],
        "response_text": "Proposal: add a regression test before changing dispatch.",
    })
    assert finished.status_code == 200

    response = client.get("/recovery/browser-consult/result/" + consultation_id)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["task_ref"] == "mission_1234abcd"
    assert body["response_text"].startswith("Proposal:")
    assert len(body["response_sha256"]) == 64
    assert body["result_trusted"] is False
    assert body["independence_attested"] is False
    assert body["accepted"] is None
    assert "claim_token" not in body
    assert "prompt" not in body


def test_result_endpoint_reports_missing_consultation_and_invalid_id(monkeypatch, tmp_path):
    client, _store = _client(monkeypatch, tmp_path)
    missing = client.get("/recovery/browser-consult/result/consultation_missing")
    invalid = client.get("/recovery/browser-consult/result/" + ("x" * 81))
    assert missing.status_code == 404
    assert invalid.status_code == 400


def test_result_endpoint_requires_authenticated_operator_scope():
    route = classify_request_path(
        "/recovery/browser-consult/result/consultation_123", "GET"
    )
    assert route is not None
    assert route.scope is SecurityScope.BROWSER_CONSULT_CONTROL
