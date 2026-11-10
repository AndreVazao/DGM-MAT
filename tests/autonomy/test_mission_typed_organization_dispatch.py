"""MissionEngine surface for typed, receipt-backed organization task execution."""
from core.autonomy.mission_engine import MissionEngine
from core.organization.message_bus import InternalMessageBus
from core.organization.models import AgentStatus, Task, TaskStatus


def test_mission_engine_dispatches_only_typed_tasks_and_persists_receipt(tmp_path, monkeypatch):
    database = tmp_path / "organization.sqlite3"
    bus = InternalMessageBus(database)
    engine = MissionEngine(organization_bus=bus)
    agent_id = "agent:repository-cartographer"
    engine.worker_runtime.register_handler(
        agent_id,
        lambda message: {"worker": "repository-cartographer"},
        capabilities=("file-inventory", "project-tree"),
    )
    engine.organization_registry.set_status(agent_id, AgentStatus.AVAILABLE)
    task = Task(
        task_id="task:mission-engine-typed-dispatch",
        title="Inventory repository",
        mission_id="mission:typed-integration",
        description="Inspect only the repository identified by a host allowlist ID.",
        metadata={
            "task_kind": "repository_inventory",
            "repository_id": "demo",
            "required_skills": ["file-inventory", "project-tree"],
            "required_permissions": ["reports:write"],
        },
    )
    engine.create_organization_task(task)
    engine.delegate_organization_task(task.task_id)

    def verified_result(**kwargs):
        assert kwargs["task_id"] == task.task_id
        assert kwargs["agent_id"] == agent_id
        return {
            "status": "COMPLETED",
            "agent_id": agent_id,
            "message_id": "msg:mission-engine-task-receipt",
            "result": {"worker": "repository-cartographer", "status": "COMPLETED_READ_ONLY"},
            "durable_receipt": True,
        }

    monkeypatch.setattr(engine.readonly_worker_orchestrator, "run", verified_result)
    result = engine.dispatch_organization_task(task.task_id)

    assert result["status"] == "COMPLETED"
    assert result["task_status"] == TaskStatus.COMPLETED.value
    assert engine.get_organization_task(task.task_id).metadata["worker_execution"]["durable_receipt"] is True
    bus.close()

    reopened_bus = InternalMessageBus(database)
    reopened = MissionEngine(organization_bus=reopened_bus)
    restored = reopened.get_organization_task(task.task_id)
    assert restored.status is TaskStatus.COMPLETED
    assert restored.metadata["worker_execution"]["message_id"] == "msg:mission-engine-task-receipt"
    reopened_bus.close()

def test_typed_mission_waits_for_registered_worker_before_queueing():
    engine = MissionEngine(organization_bus=InternalMessageBus())
    mission = engine.create_mission(
        "inventory repository demo",
        "Typed read-only inventory requires the configured repository worker",
    )

    assert mission.status.value == "WAITING_FOR_CAPABILITY"
    readiness = mission.metadata["executor_readiness"]
    assert readiness["reason_code"] == "TYPED_WORKER_NOT_READY"
    assert readiness["required_agent"] == "agent:repository-cartographer"
    assert "action_id" not in mission.metadata


def test_typed_mission_is_queued_only_after_worker_handler_and_capabilities_exist(tmp_path, monkeypatch):
    engine = MissionEngine(organization_bus=InternalMessageBus())
    engine.missions_path = tmp_path
    agent_id = "agent:repository-cartographer"
    engine.worker_runtime.register_handler(
        agent_id,
        lambda message: {"worker": "repository-cartographer"},
        capabilities=("file-inventory", "project-tree"),
    )
    profile = engine.organization_registry.get_agent(agent_id)
    monkeypatch.setattr(profile, "status", AgentStatus.AVAILABLE)

    mission = engine.create_mission(
        "inventory repository demo",
        "Typed read-only inventory with a registered worker",
    )
    action = engine.action_queue.get_action(mission.metadata["action_id"])
    assert mission.status.value == "QUEUED"
    assert mission.metadata["executor_readiness"]["status"] == "READY"
    assert action["status"] == "APPROVED"
    assert action["approved_by"] == "system_auto"

    def verified_result(**kwargs):
        assert kwargs["agent_id"] == agent_id
        assert kwargs["task_id"].startswith("mission_task_")
        return {
            "status": "COMPLETED",
            "agent_id": agent_id,
            "message_id": "msg:mission-readiness-receipt",
            "result": {"status": "COMPLETED_READ_ONLY", "repositories": ["demo"]},
            "durable_receipt": True,
        }

    monkeypatch.setattr(engine.readonly_worker_orchestrator, "run", verified_result)
    result = engine._handle_queue_execution({"mission_id": mission.mission_id, "goal": mission.goal})

    assert mission.status.value == "COMPLETED"
    assert result["durable_receipt"] is True
    assert result["agent_id"] == agent_id

