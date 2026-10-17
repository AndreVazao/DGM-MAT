import json
from datetime import datetime
from unittest.mock import patch

from core.autonomy.mission_engine import MissionEngine
from core.autonomy.mission_models import Mission, MissionStatus


class FakeLocalProvider:
    config = {"model": "qwen2.5:1.5b", "coder_model": "qwen2.5-coder:1.5b"}

    def generate(self, messages, **kwargs):
        assert kwargs["json_mode"] is True
        return json.dumps([
            {"title": "Inspect repository", "description": "Inspect current files and identify relevant modules."},
            {"title": "Implement bounded change", "description": "Implement the smallest change with a clear acceptance criterion."},
            {"title": "Run local tests", "description": "Run targeted tests and record results without triggering remote workflows."},
        ])


def test_mission_planner_uses_local_model_and_never_executes_subtasks(tmp_path):
    engine = MissionEngine()
    engine.missions_path = tmp_path
    mission = Mission(
        mission_id="local-plan-test", goal="Implement a Python repository feature",
        description="test", status=MissionStatus.QUEUED, created_at=datetime.now(),
    )
    engine.active_missions = {mission.mission_id: mission}
    with patch("core.provider_sync.provider_registry.initialize_default_providers"), patch(
        "core.provider_sync.provider_registry.provider_registry.get_provider", return_value=FakeLocalProvider()
    ):
        subtasks = engine._build_local_subtasks(mission)
    assert len(subtasks) == 3
    assert mission.metadata["local_planning"]["provider"] == "ollama"
    assert mission.metadata["local_planning"]["automatic_subtask_execution"] is False
    assert all(item.status == "pending" for item in subtasks)


def test_mission_planner_falls_back_without_crashing_when_local_provider_fails(tmp_path):
    engine = MissionEngine()
    engine.missions_path = tmp_path
    mission = Mission(
        mission_id="local-plan-fallback-test", goal="Plan a task",
        description="test", status=MissionStatus.QUEUED, created_at=datetime.now(),
    )
    engine.active_missions = {mission.mission_id: mission}
    class BrokenProvider:
        config = {"model": "qwen2.5:1.5b", "coder_model": "qwen2.5-coder:1.5b"}
        def generate(self, messages, **kwargs):
            raise RuntimeError("offline")
    with patch("core.provider_sync.provider_registry.initialize_default_providers"), patch(
        "core.provider_sync.provider_registry.provider_registry.get_provider", return_value=BrokenProvider()
    ):
        assert engine._build_local_subtasks(mission) is None
    assert mission.metadata["local_planning"]["status"] == "DETERMINISTIC_FALLBACK"
