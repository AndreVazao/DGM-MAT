import pytest
from core.autonomy.mission_engine import MissionEngine
from core.organization.message_bus import InternalMessageBus
from core.autonomy.mission_models import MissionStatus
from core.autonomy.active_runtime.objective_engine import ObjectiveEngine

def test_mission_lifecycle():
    engine = MissionEngine(organization_bus=InternalMessageBus())
    mission = engine.create_mission("Test Goal", "Test Description")
    assert mission.mission_id.startswith("mission_")
    assert mission.status == MissionStatus.QUEUED

    subtasks = engine.decompose_mission(mission.mission_id)
    assert len(subtasks) == 3
    assert mission.status == MissionStatus.RUNNING

def test_objective_generation_with_missions():
    obj_engine = ObjectiveEngine()
    engine = MissionEngine(organization_bus=InternalMessageBus())
    mission = engine.create_mission("Build Feature X", "Desc")
    engine.decompose_mission(mission.mission_id)

    objectives = obj_engine.generate_objectives(analysis={}, active_missions=[mission])
    mission_tasks = [obj for obj in objectives if obj["type"] == "MISSION_TASK"]
    assert len(mission_tasks) == 3
    assert mission_tasks[0]["mission_id"] == mission.mission_id
    assert mission_tasks[0]["approval_required"] is True

def test_approved_generic_mission_does_not_claim_execution_without_executor():
    engine = MissionEngine(organization_bus=InternalMessageBus())
    mission = engine.create_mission(
        "Prepare a summary of the repository architecture",
        "Regression: generic planning must not masquerade as execution",
    )

    result = engine._handle_queue_execution({
        "mission_id": mission.mission_id,
        "goal": mission.goal,
    })

    assert mission.status == MissionStatus.FAILED
    assert result["status"] if "status" in result else result["error_type"] == "NotImplementedError"
    assert "no generic task executor is registered" in result["error"]
    assert mission.subtasks
    assert all(task.status != "completed" for task in mission.subtasks)
    assert mission.metadata["result"]["error_type"] == "NotImplementedError"

