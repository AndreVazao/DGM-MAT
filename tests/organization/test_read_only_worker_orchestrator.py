from __future__ import annotations

import json

from core.organization.configured_readonly_workers import (
    REPOSITORIES_ENV,
    WORKSPACE_ROOT_ENV,
    register_configured_readonly_workers,
)
from core.organization.message_bus import InternalMessageBus
from core.organization.models import Message
from core.organization.read_only_worker_orchestrator import ReadOnlyWorkerOrchestrator
from core.organization.worker_runtime import WorkerRuntime


def setup_orchestrator(tmp_path):
    workspace = tmp_path / "workspace"
    repository = workspace / "demo"
    (repository / "src").mkdir(parents=True)
    (repository / "tests" / "unit").mkdir(parents=True)
    (repository / "src" / "service.py").write_text(
        "import json\nclass Service:\n    def run(self): return True\n", encoding="utf-8"
    )
    (repository / "tests" / "unit" / "test_service.py").write_text(
        "import pytest\n@pytest.fixture\ndef client(): return object()\n"
        "def test_run(client): assert client\n", encoding="utf-8"
    )
    bus = InternalMessageBus()
    runtime = WorkerRuntime(bus)
    config = {
        WORKSPACE_ROOT_ENV: str(workspace),
        REPOSITORIES_ENV: json.dumps({"demo": "demo"}),
    }
    registration = register_configured_readonly_workers(runtime, environ=config)
    assert registration["status"] == "REGISTERED"
    return ReadOnlyWorkerOrchestrator(bus, runtime), bus, runtime


def run(orchestrator, agent_id, correlation="corr:one"):
    return orchestrator.run(
        agent_id=agent_id,
        repository_id="demo",
        mission_id="mission:dispatch-test",
        correlation_id=correlation,
    )


def test_dispatches_cartographer_and_persists_result_receipt(tmp_path):
    orchestrator, bus, _ = setup_orchestrator(tmp_path)
    result = run(orchestrator, "agent:repository-cartographer")
    assert result["status"] == "COMPLETED"
    assert result["result"]["status"] == "COMPLETED_READ_ONLY"
    assert result["durable_receipt"] is True
    receipt = bus.get_dispatch_result(result["message_id"])
    assert receipt is not None
    assert receipt["result"]["worker"] == "repository-cartographer"


def test_dispatches_python_source_analyst(tmp_path):
    orchestrator, _, _ = setup_orchestrator(tmp_path)
    result = run(orchestrator, "agent:python-source-analyst")
    assert result["status"] == "COMPLETED"
    assert result["result"]["files_analyzed"] == 1
    assert result["result"]["definitions"]["classes"] == 1
    assert result["result"]["code_executed"] is False


def test_dispatches_python_test_inventory(tmp_path):
    orchestrator, _, _ = setup_orchestrator(tmp_path)
    result = run(orchestrator, "agent:python-test-inventory")
    assert result["status"] == "COMPLETED"
    assert result["result"]["test_files_analyzed"] == 1
    assert result["result"]["test_functions"] == 1
    assert result["result"]["tests_executed"] is False


def test_same_mission_correlation_is_idempotent(tmp_path):
    orchestrator, bus, _ = setup_orchestrator(tmp_path)
    first = run(orchestrator, "agent:python-source-analyst", "corr:stable")
    second = run(orchestrator, "agent:python-source-analyst", "corr:stable")
    assert first["status"] == "COMPLETED"
    assert second["status"] == "ALREADY_COMPLETED"
    assert first["message_id"] == second["message_id"]
    assert bus.get_dispatch_result(first["message_id"]) is not None


def test_unknown_or_unregistered_worker_fails_closed(tmp_path):
    bus = InternalMessageBus()
    runtime = WorkerRuntime(bus)
    orchestrator = ReadOnlyWorkerOrchestrator(bus, runtime)
    unknown = run(orchestrator, "agent:unknown")
    assert unknown["status"] == "BLOCKED"
    assert unknown["reason"] == "worker_not_allowed"
    known = run(orchestrator, "agent:python-source-analyst")
    assert known["status"] == "BLOCKED"
    assert known["reason"] == "worker_handler_not_registered"


def test_older_inbox_message_is_not_misreported_as_current_task(tmp_path):
    orchestrator, bus, _ = setup_orchestrator(tmp_path)
    bus.send(Message(
        sender_id="agent:hq-orchestrator",
        recipient_id="agent:python-source-analyst",
        subject="Older queued request",
        body="{}",
        message_id="msg:older-request",
        mission_id="mission:older",
        correlation_id="corr:older",
    ))
    first = run(orchestrator, "agent:python-source-analyst", "corr:new")
    assert first["status"] == "QUEUED"
    assert first["reason"] == "older_inbox_message_dispatched_first"
    second = run(orchestrator, "agent:python-source-analyst", "corr:new")
    assert second["status"] == "COMPLETED"
