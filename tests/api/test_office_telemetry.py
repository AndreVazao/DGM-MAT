import json
from types import SimpleNamespace

from core.api import runtime_api


def test_office_telemetry_aggregates_real_states_without_mission_content(tmp_path, monkeypatch):
    (tmp_path / "running.json").write_text(
        json.dumps({
            "mission_id": "mission-running",
            "goal": "PRIVATE_GOAL_MUST_NOT_LEAK",
            "status": "RUNNING",
            "updated_at": "2026-10-20T10:00:00",
            "metadata": {"action_id": 17, "result": {"handler": "architecture_summary"}},
        }),
        encoding="utf-8",
    )
    (tmp_path / "queued.json").write_text(
        json.dumps({
            "mission_id": "mission-queued",
            "goal": "another private goal",
            "status": "QUEUED",
            "updated_at": "2026-10-20T09:00:00",
            "metadata": {"action_id": 18},
        }),
        encoding="utf-8",
    )
    (tmp_path / "corrupt.json").write_text("{invalid", encoding="utf-8")
    monkeypatch.setattr(runtime_api.mission_engine, "missions_path", tmp_path)

    class FakeQueue:
        def get_mission_execution_telemetry(self, limit=8):
            assert limit == 8
            return {
                "total": 2,
                "counts": {"QUEUED": 1, "APPROVED": 1},
                "recent": [{"action_id": 18, "mission_id": "mission-queued", "status": "QUEUED"}],
                "source": "test",
                "content_minimized": True,
            }

        def get_health(self):
            return {
                "worker_alive": True,
                "last_heartbeat": "2026-10-20T10:00:00",
                "handlers": ["MISSION_EXECUTION"],
            }

    monkeypatch.setattr(runtime_api, "SafeActionQueue", FakeQueue)
    monkeypatch.setattr(
        runtime_api.state_store,
        "get_snapshot",
        lambda: SimpleNamespace(runtime_status="running", is_degraded=False),
    )

    result = runtime_api.get_office_telemetry()

    assert result["schema"] == "dgm-mat.office-telemetry.v1"
    assert result["missions"]["total"] == 2
    assert result["missions"]["counts"]["RUNNING"] == 1
    assert result["missions"]["counts"]["QUEUED"] == 1
    assert result["missions"]["invalid_checkpoints"] == 1
    assert result["departments"]["engineering"]["state"] == "active"
    assert result["departments"]["approvals"]["state"] == "waiting"
    assert result["departments"]["operations"]["state"] == "active"
    assert result["departments"]["research"]["state"] == "unknown"
    assert result["departments"]["memory"]["state"] == "unknown"
    assert result["organization"]["role_state"] == "declared_catalog"
    assert result["organization"]["agents"]
    assert all(agent["activity_state"] == "unknown" for agent in result["organization"]["agents"])
    assert "PRIVATE_GOAL_MUST_NOT_LEAK" not in json.dumps(result)
    assert "another private goal" not in json.dumps(result)
    assert "goal" not in result["missions"]["recent"][0]



def test_office_telemetry_exposes_declared_roster_without_claiming_agents_are_running():
    roster = runtime_api._office_roster_snapshot()

    assert roster["source"] == "core.organization.office"
    assert roster["role_state"] == "declared_catalog"
    assert len(roster["departments"]) == len(runtime_api.OFFICE_DEPARTMENTS)
    assert len(roster["agents"]) == len(runtime_api.OFFICE_AGENTS)
    assert all(item["role_state"] == "defined" for item in roster["departments"])
    assert all(item["activity_state"] == "unknown" for item in roster["departments"])
    assert all(item["activity_state"] == "unknown" for item in roster["agents"])
    assert all(isinstance(item["execution_maturity"], str) and item["execution_maturity"] for item in roster["agents"])
    assert all("permissions" not in item for item in roster["agents"])
