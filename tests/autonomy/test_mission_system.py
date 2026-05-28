import pytest
from core.autonomy.mission_engine import MissionEngine
from core.autonomy.mission_models import MissionStatus
from core.autonomy.active_runtime.objective_engine import ObjectiveEngine

def test_mission_lifecycle():
    engine = MissionEngine()
    mission = engine.create_mission("Test Goal", "Test Description")
    assert mission.mission_id.startswith("mission_")
    assert mission.status == MissionStatus.QUEUED

    subtasks = engine.decompose_mission(mission.mission_id)
    assert len(subtasks) == 3
    assert mission.status == MissionStatus.RUNNING

def test_objective_generation_with_missions():
    obj_engine = ObjectiveEngine()
    engine = MissionEngine()
    mission = engine.create_mission("Build Feature X", "Desc")
    engine.decompose_mission(mission.mission_id)

    objectives = obj_engine.generate_objectives(analysis={}, active_missions=[mission])
    mission_tasks = [obj for obj in objectives if obj["type"] == "MISSION_TASK"]
    assert len(mission_tasks) == 3
    assert mission_tasks[0]["mission_id"] == mission.mission_id
    assert mission_tasks[0]["approval_required"] is True
