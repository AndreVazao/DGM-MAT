from __future__ import annotations

import pytest

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
