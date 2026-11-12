from __future__ import annotations

import pytest

from core.autonomy.mission_engine import MissionEngine
from core.autonomy.mission_intent_router import classify_mission_intent
from core.autonomy.mission_models import MissionStatus
from core.organization.message_bus import InternalMessageBus


@pytest.mark.parametrize(
    ("goal", "provider"),
    [
        ("abre o chatgpt", "chatgpt"),
        ("open ChatGPT", "chatgpt"),
        ("abre o Gemini", "gemini"),
        ("launch Grok", "grok"),
        ("abrir Claude", "claude"),
        ("abre o DeepSeek", "deepseek"),
        ("open Qwen", "qwen"),
    ],
)
def test_explicit_provider_launch_is_approved_and_never_sends_messages(goal, provider):
    decision = classify_mission_intent(goal)
    assert decision.intent == "browser_open_provider:" + provider
    assert decision.supported is True
    assert decision.requires_approval is True


def test_provider_launch_mission_executes_only_after_queue_approval(tmp_path, monkeypatch):
    from core.autonomy import provider_launcher

    opened = []
    monkeypatch.setattr(provider_launcher.webbrowser, "open", lambda url, new, autoraise: opened.append((url, new, autoraise)) or True)

    engine = MissionEngine(organization_bus=InternalMessageBus())
    engine.missions_path = tmp_path
    mission = engine.create_mission("abre o chatgpt", "Open the provider page; do not send a message.")

    assert mission.status == MissionStatus.QUEUED
    action = engine.action_queue.get_action(mission.metadata["action_id"])
    assert action["status"] == "QUEUED"
    assert opened == []

    assert engine.action_queue.approve(mission.metadata["action_id"], operator="test-operator")
    result = engine._handle_queue_execution({"mission_id": mission.mission_id})

    assert mission.status == MissionStatus.COMPLETED
    assert opened == [("https://chatgpt.com/", 2, True)]
    assert result["handler"] == "browser_open_provider"
    assert result["provider"] == "chatgpt"
    assert result["status"] == "OPEN_REQUESTED"
    assert result["launch_accepted_by_os"] is True
    assert result["page_load_verified"] is False
    assert result["message_sent"] is False
    assert mission.metadata["result"]["message_sent"] is False


def test_provider_launch_failure_never_claims_success(tmp_path, monkeypatch):
    from core.autonomy import provider_launcher

    monkeypatch.setattr(provider_launcher.webbrowser, "open", lambda *args, **kwargs: False)
    engine = MissionEngine(organization_bus=InternalMessageBus())
    engine.missions_path = tmp_path
    mission = engine.create_mission("open ChatGPT", "Expected launch rejection.")

    assert engine.action_queue.approve(mission.metadata["action_id"], operator="test-operator")
    with pytest.raises(RuntimeError, match="did not accept"):
        engine._handle_queue_execution({"mission_id": mission.mission_id})

    assert mission.status == MissionStatus.FAILED
    assert mission.metadata["result"]["error_type"] == "RuntimeError"


def test_unrecognized_provider_launch_is_not_routed():
    decision = classify_mission_intent("open an unknown assistant")
    assert decision.supported is False
    assert decision.requires_approval is True
