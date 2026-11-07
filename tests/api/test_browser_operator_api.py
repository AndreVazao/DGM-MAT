from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from core.api import browser_operator_api
from core.api.security_policy import SecurityScope, classify_request_path
from core.providers.browser.browser_operator_queue import BrowserOperatorQueue


def make_client(monkeypatch, tmp_path):
    queue = BrowserOperatorQueue(
        tmp_path / "browser-operator.sqlite3",
        lease_seconds=30,
        mission_status_resolver=lambda _mission_id: "RUNNING",
    )
    monkeypatch.setattr(browser_operator_api, "_queue", lambda: queue)
    app = FastAPI()

    @app.middleware("http")
    async def fake_local_session(request: Request, call_next):
        request.scope.setdefault("state", {})["dgm_principal"] = {
            "subject": "test-operator",
            "session_id": "test-extension-session",
            "scopes": ["operator", "browser-capture"],
        }
        return await call_next(request)

    app.include_router(browser_operator_api.router)
    return TestClient(app), queue


def payload(**overrides):
    value = {
        "idempotency_key": "mission-1234abcd-chatgpt-1",
        "mission_id": "mission_1234abcd",
        "provider": "chatgpt",
        "source_id": "conversation-123",
        "conversation_url": "https://chatgpt.com/c/conversation-123",
        "message": "Inspect the repository and report verified findings.",
    }
    value.update(overrides)
    return value


def test_browser_operator_routes_have_narrow_extension_scope():
    for path, method, expected in (
        ("/browser-operator/next", "GET", SecurityScope.BROWSER_CAPTURE),
        ("/browser-operator/tasks/a/result", "POST", SecurityScope.BROWSER_CAPTURE),
        ("/browser-operator/tasks/a/fail", "POST", SecurityScope.BROWSER_CAPTURE),
        ("/browser-operator/tasks", "POST", SecurityScope.OPERATOR),
        ("/browser-operator/tasks/a/approve", "POST", SecurityScope.OPERATOR),
        ("/browser-operator/tasks", "GET", SecurityScope.OPERATOR),
    ):
        route = classify_request_path(path, method)
        assert route is not None
        assert route.scope is expected


def test_mission_browser_task_route_requires_operator_scope():
    route = classify_request_path(
        "/runtime/missions/mission_1234abcd/browser-task", "POST"
    )
    assert route is not None
    assert route.scope is SecurityScope.OPERATOR


def test_operator_approval_then_extension_claim_and_result(monkeypatch, tmp_path):
    client, queue = make_client(monkeypatch, tmp_path)
    created = client.post("/browser-operator/tasks", json=payload())
    assert created.status_code == 201
    task_id = created.json()["task_id"]
    assert created.json()["status"] == "pending_approval"

    empty = client.get("/browser-operator/next?provider=chatgpt")
    assert empty.status_code == 200
    assert empty.json()["status"] == "queue_empty"

    approved = client.post(f"/browser-operator/tasks/{task_id}/approve")
    assert approved.status_code == 200
    claimed = client.get("/browser-operator/next?provider=chatgpt")
    assert claimed.status_code == 200
    task = claimed.json()["task"]
    assert task["task_id"] == task_id
    assert task["message"] == payload()["message"]

    result = client.post(
        f"/browser-operator/tasks/{task_id}/result",
        json={
            "claim_token": task["claim_token"],
            "status": "completed",
            "result": {"assistant_text": "The repository is clean."},
        },
    )
    assert result.status_code == 200
    saved = queue.get(task_id)
    assert saved["status"] == "completed"
    assert saved["result"]["assistant_text"] == "The repository is clean."


def test_invalid_provider_url_is_rejected_before_queueing(monkeypatch, tmp_path):
    client, queue = make_client(monkeypatch, tmp_path)
    response = client.post(
        "/browser-operator/tasks",
        json=payload(conversation_url="https://example.com/c/conversation-123"),
    )
    assert response.status_code == 422
    assert queue.list_tasks() == []


def test_idempotent_task_creation_returns_existing_task(monkeypatch, tmp_path):
    client, queue = make_client(monkeypatch, tmp_path)
    first = client.post("/browser-operator/tasks", json=payload())
    second = client.post("/browser-operator/tasks", json=payload())
    assert first.status_code == second.status_code == 201
    assert first.json()["task_id"] == second.json()["task_id"]
    assert len(queue.list_tasks()) == 1


def test_mission_operator_accepts_deepseek_and_qwen_with_approval_gate(monkeypatch, tmp_path):
    client, queue = make_client(monkeypatch, tmp_path)
    providers = {
        "deepseek": "https://chat.deepseek.com/a/chat/s/conversation-123",
        "qwen": "https://chat.qwen.ai/chat/conversation-123",
    }
    for provider, url in providers.items():
        body = payload()
        body.update({
            "idempotency_key": "mission-1234abcd-" + provider,
            "provider": provider,
            "source_id": "conversation-123",
            "conversation_url": url,
        })
        response = client.post("/browser-operator/tasks", json=body)
        assert response.status_code == 201, (provider, response.text)
        result = response.json()
        assert result["status"] == "pending_approval"
        assert result["approval_required"] is True
        assert queue.get(result["task_id"])["provider"] == provider

def test_direct_operator_route_cannot_disable_per_task_approval(monkeypatch, tmp_path):
    client, queue = make_client(monkeypatch, tmp_path)
    response = client.post("/browser-operator/tasks", json=payload(approval_required=False))
    assert response.status_code == 422
    assert queue.list_tasks() == []
