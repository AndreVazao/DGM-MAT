from __future__ import annotations

import pytest

from core.autonomy.mission_models import MissionStatus
from core.api.runtime_api import MissionBrowserTaskCreate


@pytest.mark.parametrize(
    ("provider", "url"),
    [
        ("deepseek", "https://chat.deepseek.com/a/chat/s/conversation-123"),
        ("qwen", "https://chat.qwen.ai/chat/conversation-123"),
    ],
)
def test_mission_browser_task_model_accepts_primary_provider(provider: str, url: str):
    task = MissionBrowserTaskCreate(
        idempotency_key="mission-task-" + provider,
        provider=provider,
        source_id="conversation-123",
        conversation_url=url,
        message="Research this technical question using the authenticated web session.",
    )
    assert task.provider == provider
    assert task.approval_required is True


def test_browser_task_without_per_task_approval_requires_running_parent_mission(monkeypatch):
    from types import SimpleNamespace

    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    import core.api.runtime_api as runtime_api
    from core.autonomy.mission_models import MissionStatus

    mission = SimpleNamespace(
        mission_id="mission_1234abcd",
        status=MissionStatus.APPROVAL_PENDING,
        metadata={},
    )

    class FakeQueue:
        def enqueue(self, **kwargs):
            return {"task_id": "browser-task-123", "status": "queued"}

    monkeypatch.setattr(runtime_api.mission_engine, "_reload_mission_checkpoint", lambda _id: mission)
    monkeypatch.setattr(runtime_api.mission_engine, "save_mission", lambda _mission: None)
    monkeypatch.setattr(runtime_api, "browser_operator_queue", lambda: FakeQueue())
    app = FastAPI()
    app.include_router(runtime_api.router)
    client = TestClient(app)
    payload = {
        "idempotency_key": "approved-mission-deepseek",
        "provider": "deepseek",
        "source_id": "conversation-123",
        "conversation_url": "https://chat.deepseek.com/a/chat/s/conversation-123",
        "message": "Ask the approved research question.",
        "approval_required": False,
    }

    pending = client.post("/runtime/missions/mission_1234abcd/browser-task", json=payload)
    assert pending.status_code == 409

    mission.status = MissionStatus.RUNNING
    approved = client.post("/runtime/missions/mission_1234abcd/browser-task", json=payload)
    assert approved.status_code == 201
    assert approved.json()["status"] == "queued"

@pytest.mark.parametrize(
    "terminal_status",
    [MissionStatus.COMPLETED, MissionStatus.CANCELLED, MissionStatus.FAILED],
)
def test_browser_task_rejects_terminal_parent_mission(monkeypatch, terminal_status):
    from types import SimpleNamespace
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    import core.api.runtime_api as runtime_api

    mission = SimpleNamespace(
        mission_id="mission_1234abcd",
        status=terminal_status,
        metadata={},
    )
    class FakeQueue:
        called = False
        def enqueue(self, **kwargs):
            self.called = True
            return {"task_id": "unexpected", "status": "queued"}

    queue = FakeQueue()
    monkeypatch.setattr(runtime_api.mission_engine, "_reload_mission_checkpoint", lambda _id: mission)
    monkeypatch.setattr(runtime_api.mission_engine, "save_mission", lambda _mission: None)
    monkeypatch.setattr(runtime_api, "browser_operator_queue", lambda: queue)
    app = FastAPI()
    app.include_router(runtime_api.router)
    client = TestClient(app)
    response = client.post(
        "/runtime/missions/mission_1234abcd/browser-task",
        json={
            "idempotency_key": "terminal-mission-task-123",
            "provider": "deepseek",
            "source_id": "conversation-123",
            "conversation_url": "https://chat.deepseek.com/a/chat/s/conversation-123",
            "message": "Do not send this after the mission has ended.",
            "approval_required": False,
        },
    )
    assert response.status_code == 409
    assert queue.called is False


def test_browser_task_rejects_missing_parent_mission(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    import core.api.runtime_api as runtime_api

    monkeypatch.setattr(runtime_api.mission_engine, "_reload_mission_checkpoint", lambda _id: None)
    app = FastAPI()
    app.include_router(runtime_api.router)
    response = TestClient(app).post(
        "/runtime/missions/mission_1234abcd/browser-task",
        json={
            "idempotency_key": "missing-mission-task-123",
            "provider": "qwen",
            "source_id": "conversation-123",
            "conversation_url": "https://chat.qwen.ai/chat/conversation-123",
            "message": "Do not send without a parent mission.",
            "approval_required": False,
        },
    )
    assert response.status_code == 404
