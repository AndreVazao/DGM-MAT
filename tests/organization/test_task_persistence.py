"""Restart and integrity tests for durable organization task lifecycle."""
import pytest

from core.organization.message_bus import InternalMessageBus
from core.organization.models import Evidence, Task, TaskStatus
from core.organization.task_manager import OrganizationTaskManager


def _task(task_id="task:persisted", **kwargs):
    title = kwargs.pop("title", "Persist lifecycle")
    description = kwargs.pop("description", "Verify restart-safe task state.")
    return Task(
        task_id=task_id,
        title=title,
        mission_id="mission:durability",
        description=description,
        **kwargs,
    )


def test_task_lifecycle_survives_bus_and_manager_reconstruction(tmp_path):
    database = tmp_path / "organization.sqlite3"
    bus = InternalMessageBus(database)
    manager = OrganizationTaskManager(bus)
    manager.create(_task(
        dependencies=["task:dependency"],
        inputs=["source.txt"],
        outputs=["report.md"],
        evidence=[Evidence(kind="test", source="pytest", summary="initial evidence")],
        approval_required=True,
        approval_reason="operator review",
        retry_count=1,
        max_retries=4,
        metadata={"required_skills": ["python"], "nested": {"safe": True}},
    ))
    manager.create(_task(
        "task:dependency",
        title="Dependency",
        description="Complete before assignment.",
    ))
    manager.transition("task:dependency", TaskStatus.COMPLETED)
    assigned = manager.assign("task:persisted", "agent:python")
    assert assigned.status is TaskStatus.ASSIGNED
    bus.close()

    reopened_bus = InternalMessageBus(database)
    reopened = OrganizationTaskManager(reopened_bus)
    restored = reopened.get("task:persisted")
    assert restored is not None
    assert restored.status is TaskStatus.ASSIGNED
    assert restored.assigned_agent == "agent:python"
    assert restored.dependencies == ["task:dependency"]
    assert restored.inputs == ["source.txt"]
    assert restored.outputs == ["report.md"]
    assert restored.approval_required is True
    assert restored.approval_reason == "operator review"
    assert restored.retry_count == 1
    assert restored.max_retries == 4
    assert restored.metadata == {"required_skills": ["python"], "nested": {"safe": True}}
    assert restored.evidence[0].summary == "initial evidence"
    assert reopened.dependencies_satisfied("task:persisted") is True
    reopened.transition("task:persisted", TaskStatus.COMPLETED)
    reopened_bus.close()

    final_bus = InternalMessageBus(database)
    final = OrganizationTaskManager(final_bus)
    assert final.get("task:persisted").status is TaskStatus.COMPLETED
    final_bus.close()


def test_duplicate_task_ids_are_rejected_without_overwriting_durable_state(tmp_path):
    bus = InternalMessageBus(tmp_path / "organization.sqlite3")
    manager = OrganizationTaskManager(bus)
    original = _task()
    manager.create(original)
    with pytest.raises(ValueError, match="already exists"):
        manager.create(_task(title="Different title"))
    assert manager.get(original.task_id).title == "Persist lifecycle"
    bus.close()

    reopened_bus = InternalMessageBus(tmp_path / "organization.sqlite3")
    assert OrganizationTaskManager(reopened_bus).get(original.task_id).title == "Persist lifecycle"
    reopened_bus.close()


def test_stale_manager_cannot_overwrite_a_newer_task_revision(tmp_path):
    database = tmp_path / "organization.sqlite3"
    first_bus = InternalMessageBus(database)
    first = OrganizationTaskManager(first_bus)
    first.create(_task())
    second_bus = InternalMessageBus(database)
    second = OrganizationTaskManager(second_bus)

    first.transition("task:persisted", TaskStatus.RUNNING)
    with pytest.raises(RuntimeError, match="revision conflict"):
        second.transition("task:persisted", TaskStatus.BLOCKED)

    assert second.get("task:persisted").status is TaskStatus.CREATED
    first_bus.close()
    second_bus.close()

    verify_bus = InternalMessageBus(database)
    assert OrganizationTaskManager(verify_bus).get("task:persisted").status is TaskStatus.RUNNING
    verify_bus.close()


def test_malformed_task_record_fails_closed_and_remains_inspectable(tmp_path):
    bus = InternalMessageBus(tmp_path / "organization.sqlite3")
    bus.save_task_record("task:broken", {"task_id": "task:broken", "status": "NOT_A_STATUS"})
    with pytest.raises(RuntimeError, match="record was retained"):
        OrganizationTaskManager(bus)
    records = bus.load_task_records()
    assert len(records) == 1
    assert records[0]["task_id"] == "task:broken"
    assert "NOT_A_STATUS" in records[0]["payload_json"]
    bus.close()


def test_unsupported_schema_version_fails_closed_without_deleting_record(tmp_path):
    bus = InternalMessageBus(tmp_path / "organization.sqlite3")
    bus.save_task_record("task:future", {
        "task_id": "task:future",
        "title": "Future",
        "mission_id": "mission:future",
        "description": "Future schema",
        "status": "CREATED",
        "created_at": "2026-11-07T00:00:00+00:00",
        "updated_at": "2026-11-07T00:00:00+00:00",
    }, schema_version=99)
    with pytest.raises(RuntimeError, match="Unsupported task schema version"):
        OrganizationTaskManager(bus)
    assert bus.load_task_records()[0]["schema_version"] == 99
    bus.close()


def test_get_returns_a_copy_and_does_not_allow_unpersisted_mutation(tmp_path):
    bus = InternalMessageBus(tmp_path / "organization.sqlite3")
    manager = OrganizationTaskManager(bus)
    manager.create(_task(metadata={"safe": True}))
    detached = manager.get("task:persisted")
    detached.metadata["safe"] = False
    assert manager.get("task:persisted").metadata["safe"] is True
    bus.close()
