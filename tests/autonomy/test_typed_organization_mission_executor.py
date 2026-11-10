from __future__ import annotations

from types import SimpleNamespace

import pytest

from core.autonomy.mission_intent_router import classify_mission_intent
from core.autonomy.typed_organization_mission_executor import TypedOrganizationMissionExecutor
from core.organization.models import TaskStatus


@pytest.mark.parametrize(
    ("goal", "intent"),
    [
        ("inventory repository DGM-MAT", "organization_repository_inventory"),
        ("inventaria repositorio DGM-MAT", "organization_repository_inventory"),
        ("analyze Python source in repository DGM-MAT", "organization_python_source_analysis"),
        ("analisa codigo python no repositorio DGM-MAT", "organization_python_source_analysis"),
        ("inventory Python tests in repository DGM-MAT", "organization_python_test_inventory"),
        ("inventaria testes python no repositorio DGM-MAT", "organization_python_test_inventory"),
    ],
)
def test_exact_typed_worker_intents_preserve_hyphenated_repository_ids(goal, intent):
    decision = classify_mission_intent(goal)
    assert decision.intent == intent
    assert decision.supported is True
    assert decision.requires_approval is False


@pytest.mark.parametrize(
    "goal",
    [
        "inventory repository DGM-MAT and delete branches",
        "analyze Python source in repository ../../Windows",
        "run tests in repository DGM-MAT",
        "please do anything useful in DGM-MAT",
    ],
)
def test_ambiguous_or_mutating_requests_do_not_match_typed_workers(goal):
    decision = classify_mission_intent(goal)
    assert decision.supported is False
    assert decision.requires_approval is True


class _TaskStore:
    def __init__(self):
        self.items = {}

    def create(self, task):
        self.items[task.task_id] = task

    def get(self, task_id):
        return self.items.get(task_id)


class _Delegation:
    def delegate(self, task_id):
        task = self.tasks.get(task_id)
        task.assigned_agent = "agent:repository-cartographer"
        task.status = TaskStatus.ASSIGNED
        return SimpleNamespace(agent_id=task.assigned_agent)


class _Dispatcher:
    TASK_KINDS = {
        "repository_inventory": {
            "agent_id": "agent:repository-cartographer",
            "capabilities": ("file-inventory", "project-tree"),
        },
        "python_source_analysis": {
            "agent_id": "agent:python-source-analyst",
            "capabilities": ("python-source-analysis",),
        },
        "python_test_inventory": {
            "agent_id": "agent:python-test-inventory",
            "capabilities": ("python-test-inventory",),
        },
    }

    def __init__(self, tasks, *, matching_receipt=True):
        self.tasks = tasks
        self.matching_receipt = matching_receipt

    def dispatch(self, task_id):
        task = self.tasks.get(task_id)
        task.status = TaskStatus.COMPLETED
        result = {"status": "COMPLETED", "files_scanned": 3}
        message_id = "msg:durable-worker-result"
        task.metadata["worker_execution"] = {
            "durable_receipt": True,
            "message_id": message_id if self.matching_receipt else "msg:other",
            "result": result,
        }
        return {
            "status": "COMPLETED",
            "durable_receipt": True,
            "message_id": message_id,
            "result": result,
        }


def _executor(matching_receipt=True):
    tasks = _TaskStore()
    delegation = _Delegation()
    delegation.tasks = tasks
    dispatcher = _Dispatcher(tasks, matching_receipt=matching_receipt)
    return TypedOrganizationMissionExecutor(tasks, delegation, dispatcher)


def test_typed_worker_requires_persisted_receipt_bound_to_result():
    mission = SimpleNamespace(
        mission_id="mission_test_123",
        goal="inventory repository DGM-MAT",
    )
    result = _executor().execute(mission, "organization_repository_inventory")
    assert result["repository_id"] == "DGM-MAT"
    assert result["durable_receipt"] is True
    assert result["read_only"] is True
    assert result["code_mutation"] is False
    assert result["message_id"] == "msg:durable-worker-result"


def test_typed_worker_rejects_receipt_mismatch():
    mission = SimpleNamespace(
        mission_id="mission_test_124",
        goal="inventory repository DGM-MAT",
    )
    with pytest.raises(RuntimeError, match="does not match"):
        _executor(matching_receipt=False).execute(
            mission, "organization_repository_inventory"
        )


def test_typed_worker_rejects_unknown_intent():
    mission = SimpleNamespace(mission_id="mission_test_125", goal="inventory repository DGM-MAT")
    with pytest.raises(ValueError, match="No typed organization executor"):
        _executor().execute(mission, "unsupported")



def test_mission_engine_routes_typed_inventory_through_registered_executor(tmp_path, monkeypatch):
    from core.autonomy.mission_engine import MissionEngine
    from core.autonomy.mission_models import MissionStatus
    from core.organization.message_bus import InternalMessageBus

    engine = MissionEngine(organization_bus=InternalMessageBus())
    engine.missions_path = tmp_path
    from core.organization.models import AgentStatus
    agent_id = "agent:repository-cartographer"
    engine.worker_runtime.register_handler(
        agent_id,
        lambda message: {"worker": "repository-cartographer"},
        capabilities=("file-inventory", "project-tree"),
    )
    engine.organization_registry.set_status(agent_id, AgentStatus.AVAILABLE)
    monkeypatch.setattr(engine, "_sync_state", lambda mission: None)
    monkeypatch.setattr(engine, "_emit_mission_result", lambda mission, result: None)
    monkeypatch.setattr(engine, "_record_execution_observation", lambda mission, result, status: None)
    monkeypatch.setattr(
        engine.typed_organization_mission_executor,
        "execute",
        lambda mission, intent: {
            "handler": intent,
            "output": "Read-only inventory completed for DGM-MAT.",
            "summary": "Inventory completed",
            "task_id": "mission_task_test",
            "repository_id": "DGM-MAT",
            "agent_id": "agent:repository-cartographer",
            "message_id": "msg:test-receipt",
            "durable_receipt": True,
            "read_only": True,
            "code_mutation": False,
            "result": {"status": "COMPLETED", "files_scanned": 1},
        },
    )

    mission = engine.create_mission("inventory repository DGM-MAT", "Read-only repository inventory")
    action = engine.action_queue.get_action(mission.metadata["action_id"])
    assert action["status"] == "APPROVED"
    result = engine._handle_queue_execution({"mission_id": mission.mission_id})

    assert mission.status is MissionStatus.COMPLETED
    assert result["handler"] == "organization_repository_inventory"
    assert result["durable_receipt"] is True
    assert mission.metadata["result"]["repository_id"] == "DGM-MAT"
