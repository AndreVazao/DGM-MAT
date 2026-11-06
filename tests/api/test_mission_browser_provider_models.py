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
