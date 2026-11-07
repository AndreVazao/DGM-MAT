"""MissionEngine integration for the durable organization task store."""
from core.autonomy.mission_engine import MissionEngine
from core.organization.message_bus import InternalMessageBus
from core.organization.models import AgentStatus, Task, TaskStatus


def test_mission_engine_restores_tasks_from_its_existing_organization_bus(tmp_path):
    database = tmp_path / "organization.sqlite3"
    first_bus = InternalMessageBus(database)
    first = MissionEngine(organization_bus=first_bus)

    readiness = first.organization_readiness()
    assert readiness["task_store"] == {
        "backend": "sqlite",
        "durable": True,
        "schema_version": 1,
    }
    created = first.create_organization_task(
        Task(
            task_id="task:mission-engine-persisted",
            title="Persist through MissionEngine",
            mission_id="mission:integration",
            description="Use the already configured organization bus.",
            metadata={"required_skills": ["python"]},
        )
    )
    assert created.status is TaskStatus.CREATED
    first_bus.close()

    second_bus = InternalMessageBus(database)
    second = MissionEngine(organization_bus=second_bus)
    restored = second.get_organization_task("task:mission-engine-persisted")
    assert restored is not None
    assert restored.mission_id == "mission:integration"
    assert restored.metadata == {"required_skills": ["python"]}
    assert restored.status is TaskStatus.CREATED
    second_bus.close()


def test_mission_engine_delegates_only_to_a_registered_capability_compatible_handler(tmp_path):
    bus = InternalMessageBus(tmp_path / "organization.sqlite3")
    engine = MissionEngine(organization_bus=bus)
    agent_id = "agent:repository-cartographer"

    engine.worker_runtime.register_handler(
        agent_id,
        lambda message: {"accepted": True},
        capabilities=("file-inventory", "project-tree"),
    )
    engine.organization_registry.set_status(agent_id, AgentStatus.AVAILABLE)
    task = Task(
        task_id="task:mission-engine-delegation",
        title="Inventory allowlisted repository",
        mission_id="mission:integration",
        description="A typed task contract, not executable instructions.",
        metadata={
            "required_skills": ["file-inventory", "project-tree"],
            "required_permissions": ["reports:write"],
        },
    )
    engine.create_organization_task(task)

    decision = engine.delegate_organization_task(task.task_id)

    assert decision.agent_id == agent_id
    assigned = engine.get_organization_task(task.task_id)
    assert assigned.status is TaskStatus.ASSIGNED
    assert assigned.assigned_agent == agent_id
    bus.close()


def test_memory_only_test_bus_is_not_reported_as_durable():
    engine = MissionEngine(organization_bus=InternalMessageBus())
    readiness = engine.organization_readiness()
    assert readiness["task_store"]["backend"] == "memory"
    assert readiness["task_store"]["durable"] is False
    assert readiness["task_validated"] is False
