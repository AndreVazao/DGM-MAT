"""Tests for the DGM-MAT digital organization foundation."""

from core.organization import (
    AgentProfile,
    AgentRegistry,
    AgentStatus,
    Department,
    InternalMessageBus,
    Message,
    OrganizationTaskManager,
    OrganizationWorkspace,
    Task,
    TaskStatus,
)


def test_registry_requires_known_department():
    registry = AgentRegistry()
    try:
        registry.register_agent(
            AgentProfile(
                agent_id="agent:python",
                name="Python Engineer",
                department_id="engineering",
                role="python",
            )
        )
    except ValueError as exc:
        assert "Unknown department" in str(exc)
    else:
        raise AssertionError("Unknown departments must be rejected.")


def test_registry_registers_department_and_agent():
    registry = AgentRegistry()
    registry.register_department(
        Department("engineering", "Engineering", "Build and maintain software.")
    )
    registry.register_agent(
        AgentProfile(
            agent_id="agent:python",
            name="Python Engineer",
            department_id="engineering",
            role="python",
        )
    )
    assert registry.get_agent("agent:python").status == AgentStatus.AVAILABLE


def test_message_bus_delivers_and_tracks_read_state():
    bus = InternalMessageBus()
    message = Message(
        sender_id="agent:orchestrator",
        recipient_id="agent:python",
        subject="Implement task",
        body="Please inspect the backend contract.",
        requires_response=True,
    )
    bus.send(message)
    assert bus.receive("agent:python", unread_only=True) == [message]
    bus.mark_read("agent:python", message.message_id)
    assert bus.receive("agent:python", unread_only=True) == []


def test_task_manager_enforces_dependencies():
    manager = OrganizationTaskManager()
    manager.create(Task("task:a", "A", "mission:1", "First"))
    manager.create(
        Task(
            "task:b",
            "B",
            "mission:1",
            "Second",
            dependencies=["task:a"],
        )
    )
    assert manager.ready_tasks()[0].task_id == "task:a"
    try:
        manager.assign("task:b", "agent:python")
    except ValueError as exc:
        assert "unsatisfied dependencies" in str(exc)
    else:
        raise AssertionError("Dependent task must not be assignable yet.")
    manager.transition("task:a", TaskStatus.COMPLETED)
    manager.assign("task:b", "agent:python")
    assert manager.get("task:b").status == TaskStatus.ASSIGNED


def test_workspace_is_non_destructive(tmp_path):
    workspace = OrganizationWorkspace(tmp_path / "DGM-MAT-WORKSPACE")
    sentinel = workspace.root / "sentinel.txt"
    workspace.root.mkdir(parents=True)
    sentinel.write_text("preserve", encoding="utf-8")
    workspace.initialize()
    workspace.initialize_project("demo")
    assert sentinel.read_text(encoding="utf-8") == "preserve"
    assert (workspace.root / "projects" / "demo" / "context").is_dir()
