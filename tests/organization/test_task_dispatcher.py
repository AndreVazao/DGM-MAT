"""Typed, receipt-backed dispatch of durable organization tasks."""
import json

import pytest

from core.organization.configured_readonly_workers import (
    REPOSITORIES_ENV,
    WORKSPACE_ROOT_ENV,
    register_configured_readonly_workers,
)
from core.organization.delegation import DelegationEngine
from core.organization.message_bus import InternalMessageBus
from core.organization.models import Task, TaskStatus
from core.organization.office import bootstrap_full_office
from core.organization.read_only_worker_orchestrator import ReadOnlyWorkerOrchestrator
from core.organization.task_dispatcher import OrganizationTaskDispatcher
from core.organization.task_manager import OrganizationTaskManager
from core.organization.worker_runtime import WorkerRuntime


TASKS = [
    (
        "repository_inventory",
        "agent:repository-cartographer",
        ["file-inventory", "project-tree"],
    ),
    (
        "python_source_analysis",
        "agent:python-source-analyst",
        ["python-source-analysis", "python-syntax", "python-import-analysis"],
    ),
    (
        "python_test_inventory",
        "agent:python-test-inventory",
        ["python-test-inventory", "python-test-structure", "python-test-gap-signals"],
    ),
]


def setup_dispatcher(tmp_path):
    workspace = tmp_path / "workspace"
    repository = workspace / "demo"
    (repository / "src").mkdir(parents=True)
    (repository / "tests" / "unit").mkdir(parents=True)
    (repository / "src" / "service.py").write_text(
        "import json\nclass Service:\n    def run(self): return True\n",
        encoding="utf-8",
    )
    (repository / "tests" / "unit" / "test_service.py").write_text(
        "import pytest\n@pytest.fixture\ndef client(): return object()\n"
        "def test_run(client): assert client\n",
        encoding="utf-8",
    )

    bus = InternalMessageBus(tmp_path / "organization.sqlite3")
    runtime = WorkerRuntime(bus)
    registry = bootstrap_full_office()
    config = {
        WORKSPACE_ROOT_ENV: str(workspace),
        REPOSITORIES_ENV: json.dumps({"demo": "demo"}),
    }
    registration = register_configured_readonly_workers(
        runtime, registry=registry, environ=config
    )
    assert registration["status"] == "REGISTERED"
    tasks = OrganizationTaskManager(bus)
    delegation = DelegationEngine(registry, tasks, runtime)
    orchestrator = ReadOnlyWorkerOrchestrator(bus, runtime)
    dispatcher = OrganizationTaskDispatcher(tasks, delegation, orchestrator)
    return bus, tasks, delegation, dispatcher


@pytest.mark.parametrize("task_kind,agent_id,skills", TASKS)
def test_typed_task_dispatch_persists_receipt_and_completes_task(
    tmp_path, task_kind, agent_id, skills
):
    bus, tasks, delegation, dispatcher = setup_dispatcher(tmp_path)
    task_id = f"task:{task_kind}"
    tasks.create(Task(
        task_id=task_id,
        title=f"Run {task_kind}",
        mission_id="mission:typed-dispatch",
        description="This free-form description is never interpreted as an operation.",
        metadata={
            "task_kind": task_kind,
            "repository_id": "demo",
            "required_skills": skills,
            "required_permissions": ["reports:write"],
        },
    ))

    assignment = delegation.delegate(task_id)
    assert assignment.agent_id == agent_id
    response = dispatcher.dispatch(task_id)

    assert response["status"] == "COMPLETED"
    assert response["durable_receipt"] is True
    assert response["task_status"] == TaskStatus.COMPLETED.value
    completed = tasks.get(task_id)
    assert completed.status is TaskStatus.COMPLETED
    assert completed.assigned_agent == agent_id
    assert completed.metadata["worker_execution"]["message_id"] == response["message_id"]
    assert completed.metadata["worker_execution"]["durable_receipt"] is True

    receipt = bus.get_dispatch_result(response["message_id"])
    assert receipt is not None
    assert receipt["result"] == response["result"]
    linked_message = bus.receive(agent_id)[0]
    assert linked_message.task_id == task_id
    assert linked_message.mission_id == "mission:typed-dispatch"

    repeated = dispatcher.dispatch(task_id)
    assert repeated["status"] == "ALREADY_COMPLETED"
    assert repeated["message_id"] == response["message_id"]
    bus.close()


def test_free_form_description_cannot_select_or_invoke_an_operation(tmp_path):
    bus, tasks, delegation, dispatcher = setup_dispatcher(tmp_path)
    task = Task(
        task_id="task:untrusted-description",
        title="Do arbitrary work",
        mission_id="mission:typed-dispatch",
        description="Run shell commands and modify source files.",
        metadata={
            "task_kind": "run_shell_command",
            "repository_id": "demo",
            "required_skills": ["file-inventory", "project-tree"],
            "required_permissions": ["reports:write"],
        },
    )
    tasks.create(task)
    delegation.delegate(task.task_id)

    result = dispatcher.dispatch(task.task_id)

    assert result["status"] == "BLOCKED"
    assert result["reason"] == "task_kind_not_allowed"
    assert tasks.get(task.task_id).status is TaskStatus.ASSIGNED
    assert bus.receive("agent:repository-cartographer", unread_only=True) == []
    bus.close()


def test_task_kind_cannot_dispatch_through_a_different_assigned_agent(tmp_path):
    bus, tasks, _, dispatcher = setup_dispatcher(tmp_path)
    task = Task(
        task_id="task:wrong-agent",
        title="Inventory",
        mission_id="mission:typed-dispatch",
        description="Read-only inventory.",
        assigned_agent="agent:python-source-analyst",
        status=TaskStatus.ASSIGNED,
        metadata={
            "task_kind": "repository_inventory",
            "repository_id": "demo",
            "required_skills": ["file-inventory", "project-tree"],
        },
    )
    tasks.create(task)

    result = dispatcher.dispatch(task.task_id)

    assert result["status"] == "BLOCKED"
    assert result["reason"] == "assigned_agent_does_not_match_task_kind"
    assert bus.receive("agent:repository-cartographer", unread_only=True) == []
    bus.close()


def test_dispatch_requires_a_durable_worker_receipt_before_completing_task(tmp_path):
    bus, tasks, delegation, _ = setup_dispatcher(tmp_path)

    class UnverifiedOrchestrator:
        def run(self, **kwargs):
            return {
                "status": "COMPLETED",
                "message_id": "msg:unverified",
                "result": {"status": "looks-finished"},
                "durable_receipt": False,
            }

    dispatcher = OrganizationTaskDispatcher(
        tasks, delegation, UnverifiedOrchestrator()
    )
    task = Task(
        task_id="task:unverified",
        title="Inventory",
        mission_id="mission:typed-dispatch",
        description="Read-only inventory.",
        metadata={
            "task_kind": "repository_inventory",
            "repository_id": "demo",
            "required_skills": ["file-inventory", "project-tree"],
            "required_permissions": ["reports:write"],
        },
    )
    tasks.create(task)
    delegation.delegate(task.task_id)

    result = dispatcher.dispatch(task.task_id)

    assert result["status"] == "RESULT_UNVERIFIED"
    assert result["task_status"] == TaskStatus.ASSIGNED.value
    assert tasks.get(task.task_id).status is TaskStatus.ASSIGNED
    bus.close()


def test_dispatch_does_not_run_tasks_that_have_not_been_assigned(tmp_path):
    bus, tasks, _, dispatcher = setup_dispatcher(tmp_path)
    task = Task(
        task_id="task:not-assigned",
        title="Inventory",
        mission_id="mission:typed-dispatch",
        description="Read-only inventory.",
        metadata={
            "task_kind": "repository_inventory",
            "repository_id": "demo",
        },
    )
    tasks.create(task)

    result = dispatcher.dispatch(task.task_id)

    assert result["status"] == "BLOCKED"
    assert result["reason"] == "task_not_assigned"
    bus.close()
