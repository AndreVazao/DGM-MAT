import pytest

from core.autonomy.mission_engine import MissionEngine
from core.autonomy.mission_intent_router import classify_mission_intent
from core.autonomy.mission_models import MissionStatus


@pytest.mark.parametrize(
    ("goal", "expected_intent"),
    [
        ("show system summary", "system_summary"),
        ("show active AI engines", "engines_inventory"),
        ("check Ollama status", "ollama_status"),
        ("check Claude Code version", "claude_status"),
    ],
)
def test_read_only_diagnostic_intents_are_explicitly_allowlisted(goal, expected_intent):
    decision = classify_mission_intent(goal)

    assert decision.intent == expected_intent
    assert decision.supported is True
    assert decision.requires_approval is False


def test_system_summary_mission_executes_fixed_command_and_persists_result(tmp_path, monkeypatch):
    engine = MissionEngine()
    engine.missions_path = tmp_path
    monkeypatch.setattr(engine, "_sync_state", lambda mission: None)
    monkeypatch.setattr(engine, "_emit_mission_result", lambda mission, result: None)
    monkeypatch.setattr(engine, "_record_execution_observation", lambda mission, result, status: None)

    calls = []

    def fake_execute(command_id):
        calls.append(command_id)
        return {
            "schema": "dgm-mat.command-result.v1",
            "command_id": command_id,
            "risk": "READ",
            "status": "passed",
            "returncode": 0,
            "stdout": '{"OS":"Windows","PowerShell":"7.5","Computer":"TEST-PC"}',
            "stderr": "",
            "duration_ms": 4,
            "elevated": False,
        }

    monkeypatch.setattr(engine.command_executor, "execute", fake_execute)
    mission = engine.create_mission("show system summary", "Read-only end-to-end diagnostic")

    action = engine.action_queue.get_action(mission.metadata["action_id"])
    assert mission.status is MissionStatus.QUEUED
    assert action["status"] == "APPROVED"
    assert action["is_approved"] is True

    result = engine._handle_queue_execution({"mission_id": mission.mission_id})

    assert calls == ["system.summary"]
    assert mission.status is MissionStatus.COMPLETED
    assert result["status"] == "completed"
    assert result["handler"] == "system_summary"
    assert result["command_id"] == "system.summary"
    assert result["read_only"] is True
    assert result["elevated"] is False
    assert "TEST-PC" in result["output"]
    assert mission.metadata["result"]["command_id"] == "system.summary"
