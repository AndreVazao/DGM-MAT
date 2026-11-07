from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from core.api import browser_consult_api
from core.api.security_policy import SecurityScope, classify_request_path
from core.recovery.browser_consult_store import BrowserConsultStore


def make_client(monkeypatch, tmp_path):
    monkeypatch.setenv("DGM_BROWSER_CONSULT_ENABLED", "1")
    monkeypatch.setenv("DGM_BROWSER_CONSULT_FREE_PROVIDERS", "chatgpt,gemini,grok,deepseek,qwen")
    store = BrowserConsultStore(tmp_path / "consult.sqlite3")
    monkeypatch.setattr(browser_consult_api, "_store", lambda: store)
    monkeypatch.setattr(browser_consult_api, "_audit", lambda *args, **kwargs: None)
    app = FastAPI()

    @app.middleware("http")
    async def fake_local_session(request: Request, call_next):
        request.scope.setdefault("state", {})["dgm_principal"] = {
            "subject": "test-operator",
            "session_id": "test-extension-session",
            "scopes": ["operator", "browser-capture"],
        }
        return await call_next(request)

    app.include_router(browser_consult_api.router)
    return TestClient(app), store


def test_consult_routes_have_operator_and_extension_scopes():
    expected = (
        ("/recovery/browser-consult/status", "GET", SecurityScope.OPERATOR),
        ("/recovery/browser-consult/enqueue", "POST", SecurityScope.OPERATOR),
        ("/recovery/browser-consult/approve/consultation_123", "POST", SecurityScope.OPERATOR),
        ("/recovery/browser-consult/next", "POST", SecurityScope.BROWSER_CAPTURE),
        ("/recovery/browser-consult/result", "POST", SecurityScope.BROWSER_CAPTURE),
        ("/recovery/browser-consult/block", "POST", SecurityScope.BROWSER_CAPTURE),
    )
    for path, method, scope in expected:
        route = classify_request_path(path, method)
        assert route is not None
        assert route.scope is scope


def test_consultation_requires_operator_approval_and_claim_token(monkeypatch, tmp_path):
    client, store = make_client(monkeypatch, tmp_path)
    queued = client.post("/recovery/browser-consult/enqueue", json={
        "task_ref": "mission_1234abcd",
        "goal": "Review this bounded technical question",
        "context": "Only use the minimal redacted context.",
        "providers": ["chatgpt", "deepseek"],
        "free_capacity_confirmed": True,
    })
    assert queued.status_code == 200
    body = queued.json()
    assert body["status"] == "PENDING_APPROVAL"
    assert body["approval_required"] is True
    consultation_id = body["consultation_ids"][0]

    empty = client.post("/recovery/browser-consult/next?provider=chatgpt", json={})
    assert empty.status_code == 200
    assert empty.json()["status"] == "queue_empty"

    approved = client.post("/recovery/browser-consult/approve/" + consultation_id)
    assert approved.status_code == 200
    claimed = client.post("/recovery/browser-consult/next?provider=chatgpt", json={})
    assert claimed.status_code == 200
    item = claimed.json()["next"]
    assert item["consultation_id"] == consultation_id
    assert len(item["claim_token"]) >= 32

    wrong = client.post("/recovery/browser-consult/result", json={
        "consultation_id": consultation_id,
        "claim_token": "x" * 40,
        "response_text": "This must not be stored.",
    })
    assert wrong.status_code == 409

    result = client.post("/recovery/browser-consult/result", json={
        "consultation_id": consultation_id,
        "claim_token": item["claim_token"],
        "response_text": "Independent opinion: verify the race condition with a test.",
    })
    assert result.status_code == 200
    assert result.json()["result_trusted"] is False
    assert store.status()["counts"]["COMPLETED"] == 1


def test_consultation_requires_free_capacity_attestation(monkeypatch, tmp_path):
    client, store = make_client(monkeypatch, tmp_path)
    response = client.post("/recovery/browser-consult/enqueue", json={
        "task_ref": "mission_1234abcd",
        "goal": "Review a technical assumption",
        "providers": ["qwen"],
        "free_capacity_confirmed": False,
    })
    assert response.status_code == 400
    assert store.status()["counts"] == {}


def test_consultation_api_rejects_missing_principal(monkeypatch, tmp_path):
    monkeypatch.setenv("DGM_BROWSER_CONSULT_ENABLED", "1")
    monkeypatch.setenv("DGM_BROWSER_CONSULT_FREE_PROVIDERS", "chatgpt")
    monkeypatch.setattr(browser_consult_api, "_store", lambda: BrowserConsultStore(tmp_path / "consult.sqlite3"))
    app = FastAPI()
    app.include_router(browser_consult_api.router)
    response = TestClient(app).get("/recovery/browser-consult/status")
    assert response.status_code == 401
