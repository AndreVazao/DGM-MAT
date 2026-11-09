"""Regression matrix for the real mission lifecycle and its safety boundaries.

These tests deliberately distinguish mission creation, approval, execution and
verified completion. A proposed plan is never accepted as execution evidence.
"""
from __future__ import annotations

import pytest

from core.autonomy.mission_intent_router import classify_mission_intent
from core.autonomy.mission_engine import MissionEngine
from core.organization.message_bus import InternalMessageBus


@pytest.mark.parametrize(
    ("goal", "intent"),
    [
        ("show system summary", "system_summary"),
        ("show active AI engines", "engines_inventory"),
        ("check Ollama status", "ollama_status"),
        ("check Claude Code version", "claude_status"),
        ("show repository status", "repository_status"),
        ("research the local repository for approval queue", "local_research"),
    ],
)
def test_known_read_only_mission_routes_are_explicit(goal: str, intent: str) -> None:
    decision = classify_mission_intent(goal)
    assert decision.intent == intent
    assert decision.supported is True
    assert decision.requires_approval is False


@pytest.mark.parametrize(
    "goal",
    [
        "recover conversations from the AI assistants",
        "fix the DGM-MAT executor",
        "run a full-day autonomous coding mission",
        "install all pending updates and restart services",
        "delete obsolete branches and clean repositories",
        "ask Claude Code to implement a new feature",
    ],
)
def test_unregistered_or_mutating_work_never_receives_automatic_approval(goal: str) -> None:
    decision = classify_mission_intent(goal)
    assert decision.supported is False
    assert decision.requires_approval is True


def test_unsupported_mission_is_queued_for_operator_not_auto_approved() -> None:
    engine = MissionEngine(organization_bus=InternalMessageBus())
    mission = engine.create_mission(
        "recover conversations from the AI assistants",
        "Regression: no conversation-recovery executor is registered yet",
    )
    action = engine.action_queue.get_action(mission.metadata["action_id"])

    assert mission.status.value == "QUEUED"
    assert action["status"] == "QUEUED"
    assert action["is_approved"] is False
