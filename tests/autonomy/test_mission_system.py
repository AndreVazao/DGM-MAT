import pytest
from core.autonomy.mission_engine import MissionEngine
from core.organization.message_bus import InternalMessageBus
from core.autonomy.mission_models import Mission, MissionStatus
from core.learning.learning_engine import LearningEngine
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

def test_read_only_architecture_summary_mission_executes_with_source_evidence(tmp_path):
    engine = MissionEngine(organization_bus=InternalMessageBus())
    engine.missions_path = tmp_path
    mission = engine.create_mission(
        "Prepare a summary of the repository architecture",
        "A bounded, read-only capability backed by local architecture documents",
    )

    assert mission.status == MissionStatus.QUEUED
    assert engine.action_queue.get_action(mission.metadata["action_id"])["status"] == "APPROVED"

    result = engine._handle_queue_execution({
        "mission_id": mission.mission_id,
        "goal": mission.goal,
    })

    assert mission.status == MissionStatus.COMPLETED
    assert result["handler"] == "architecture_summary"
    assert result["sources"]
    assert "README.md:L" in result["output"]
    assert "Authority and architecture boundaries" in result["output"]
    assert result["execution_duration"] >= 0
    assert mission.metadata["result"]["handler"] == "architecture_summary"
    assert mission.subtasks == []

def test_failed_mission_surfaces_local_research_evidence(tmp_path, monkeypatch):
    engine = MissionEngine(organization_bus=InternalMessageBus())
    engine.learning_engine = LearningEngine(tmp_path / "observations.jsonl")
    engine.local_mission_research = type(
        "ResearchStub",
        (),
        {"search": lambda self, goal, unknowns: {
            "status": "EVIDENCE_FOUND",
            "results": [{
                "path": "docs/executor-guide.md",
                "line": 12,
                "snippet": "No generic executor is registered.",
                "score": 1,
            }],
            "files_scanned": 4,
            "external_calls": 0,
            "commands_executed": 0,
        }},
    )()
    engine.missions_path = tmp_path
    mission = Mission(
        mission_id="mission_research_test",
        goal="Inspect executor routing",
        description="Test local evidence in failure result",
        status=MissionStatus.RUNNING,
    )
    engine.active_missions[mission.mission_id] = mission
    engine.save_mission(mission)
    monkeypatch.setattr(engine, "save_mission", lambda mission: None)
    monkeypatch.setattr(engine, "_sync_state", lambda mission: None)
    monkeypatch.setattr(engine, "_emit_mission_result", lambda mission, result: None)
    monkeypatch.setattr(
        engine, "prepare_specialist_collaboration",
        lambda mission_id, context="": {"status": "PREPARED"},
    )

    result = engine._finish_mission_failure(
        mission, NotImplementedError("No generic executor is registered")
    )

    assert mission.status == MissionStatus.FAILED
    assert mission.metadata["help_research"]["status"] == "EVIDENCE_FOUND"
    assert "docs/executor-guide.md:12" in result["output"]
    assert "No generic executor is registered." in result["output"]
    assert mission.metadata["learning_observation"]["promotion_status"] == "OBSERVATION_ONLY"



def test_unsupported_mission_does_not_auto_approve_its_queue_action():
    engine = MissionEngine(organization_bus=InternalMessageBus())
    mission = engine.create_mission(
        "Implement a new autonomous code mutator",
        "Mutating and unsupported work must stay behind human approval",
    )

    action = engine.action_queue.get_action(mission.metadata["action_id"])
    assert mission.status == MissionStatus.QUEUED
    assert action["status"] == "QUEUED"
    assert action["is_approved"] is False
