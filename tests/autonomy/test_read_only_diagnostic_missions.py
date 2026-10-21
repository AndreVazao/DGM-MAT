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


def test_claude_code_task_request_is_not_misclassified_as_a_version_check():
    decision = classify_mission_intent("I want to use Claude Code for this task")

    assert decision.intent == "unsupported"
    assert decision.supported is False
    assert decision.requires_approval is True


def _make_test_engine(tmp_path, monkeypatch):
    engine = MissionEngine()
    engine.missions_path = tmp_path
    monkeypatch.setattr(engine, "_sync_state", lambda mission: None)
    monkeypatch.setattr(engine, "_emit_mission_result", lambda mission, result: None)
    monkeypatch.setattr(engine, "_record_execution_observation", lambda mission, result, status: None)
    return engine


def test_system_summary_mission_executes_fixed_command_and_persists_result(tmp_path, monkeypatch):
    engine = _make_test_engine(tmp_path, monkeypatch)

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


@pytest.mark.parametrize(
    ("command_status", "returncode"),
    [
        ("unavailable", 127),
        ("failed", 1),
        ("timeout", None),
    ],
)
def test_diagnostic_failure_never_finishes_mission_as_completed(
    tmp_path, monkeypatch, command_status, returncode
):
    engine = _make_test_engine(tmp_path, monkeypatch)

    def fake_execute(command_id):
        return {
            "schema": "dgm-mat.command-result.v1",
            "command_id": command_id,
            "risk": "READ",
            "status": command_status,
            "returncode": returncode,
            "stdout": "",
            "stderr": "diagnostic unavailable in test",
            "duration_ms": 4,
            "elevated": False,
        }

    monkeypatch.setattr(engine.command_executor, "execute", fake_execute)
    mission = engine.create_mission("check Ollama status", "Failure-path diagnostic test")

    with pytest.raises(RuntimeError, match="Mission execution failed"):
        engine._handle_queue_execution({"mission_id": mission.mission_id})

    assert mission.status is MissionStatus.FAILED
    assert mission.status is not MissionStatus.COMPLETED
    assert mission.metadata.get("completed_at") is None
    assert mission.metadata.get("result", {}).get("status") != "completed"
