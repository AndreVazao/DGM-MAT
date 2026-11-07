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
