from core.autonomy.mission_engine import MissionEngine
from core.execution import local_coding_agent_probe


def test_mission_engine_exposes_probe_without_enabling_cli_execution(monkeypatch):
    expected = {
        "codex": {
            "agent_id": "codex",
            "available": True,
            "status": "available",
            "version": "codex-cli 1.2.3",
            "identity_verified": False,
            "billing_verified": False,
            "execution_enabled": False,
        },
        "claude_code": {
            "agent_id": "claude_code",
            "available": False,
            "status": "not_installed",
            "version": None,
            "identity_verified": False,
            "billing_verified": False,
            "execution_enabled": False,
        },
    }
    monkeypatch.setattr(
        local_coding_agent_probe.LocalCodingAgentProbe,
        "probe_all",
        lambda self: expected,
    )
    engine = MissionEngine()

    result = engine.probe_local_coding_agents()

    assert result == expected
    assert all(not item["execution_enabled"] for item in result.values())
