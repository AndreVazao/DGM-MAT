from __future__ import annotations

import json
import re

import pytest

from core.organization import InternalMessageBus, WorkerRuntime
from core.organization.models import Message
from core.organization.repository_cartographer_worker import RepositoryCartographerWorker


def make_message(body, *, sender="agent:hq-orchestrator", mission="mission:inventory", correlation="corr:inventory"):
    return Message(
        sender_id=sender,
        recipient_id=RepositoryCartographerWorker.agent_id,
        subject="Read-only repository inventory",
        body=body,
        mission_id=mission,
        correlation_id=correlation,
    )


def make_worker(tmp_path, **kwargs):
    allowed = tmp_path / "workspace"
    repo = allowed / "demo"
    repo.mkdir(parents=True)
    (repo / "main.py").write_text("PRIVATE_SOURCE_CONTENT", encoding="utf-8")
    (repo / ".env").write_text("SECRET_VALUE_DO_NOT_RETURN", encoding="utf-8")
    return RepositoryCartographerWorker(
        allowed_root=allowed,
        repositories={"demo": repo},
        **kwargs,
    ), repo


def request(repository_id="demo"):
    return json.dumps({
        "schema_version": 1,
        "operation": "inventory_repository",
        "repository_id": repository_id,
    })


def test_valid_request_returns_bounded_inventory_without_source_contents(tmp_path):
    worker, repo = make_worker(tmp_path)
    before = {path.name: path.read_bytes() for path in repo.iterdir() if path.is_file()}

    result = worker(make_message(request()))

    assert result["status"] == "COMPLETED_READ_ONLY"
    assert result["repository_id"] == "demo"
    assert result["counts"]["files"] == 2
    assert result["counts"]["sensitive_names_detected"] == 1
    assert all(item["path"] != ".env" for item in result["sample"])
    assert "PRIVATE_SOURCE_CONTENT" not in json.dumps(result)
    assert "SECRET_VALUE_DO_NOT_RETURN" not in json.dumps(result)
    assert result["source_content_read"] is False
    assert result["commands_executed"] is False
    assert result["files_modified"] is False
    assert result["network_used"] is False
    assert re.fullmatch(r"[0-9a-f]{64}", result["inventory_sha256"])
    after = {path.name: path.read_bytes() for path in repo.iterdir() if path.is_file()}
    assert after == before


@pytest.mark.parametrize(
    ("body", "reason"),
    [
        ("not-json", "request_json_invalid"),
        ("{}", "request_schema_invalid"),
        (json.dumps({"schema_version": 2, "operation": "inventory_repository", "repository_id": "demo"}), "request_schema_version_unsupported"),
        (json.dumps({"schema_version": 1, "operation": "shell", "repository_id": "demo"}), "operation_not_allowed"),
        (json.dumps({"schema_version": 1, "operation": "inventory_repository", "repository_id": "../outside"}), "repository_id_invalid"),
        (request("not-allowlisted"), "repository_not_allowlisted"),
    ],
)
def test_invalid_requests_fail_closed(tmp_path, body, reason):
    worker, _ = make_worker(tmp_path)
    result = worker(make_message(body))
    assert result["status"] == "BLOCKED"
    assert result["reason"] == reason
    assert result["files_modified"] is False
    assert result["commands_executed"] is False


def test_sender_must_be_allowlisted(tmp_path):
    worker, _ = make_worker(tmp_path)
    result = worker(make_message(request(), sender="agent:unknown"))
    assert result["status"] == "BLOCKED"
    assert result["reason"] == "sender_not_allowlisted"


def test_mission_and_correlation_are_required(tmp_path):
    worker, _ = make_worker(tmp_path)
    result = worker(make_message(request(), mission=None))
    assert result["reason"] == "mission_or_correlation_id_missing"
    result = worker(make_message(request(), correlation=None))
    assert result["reason"] == "mission_or_correlation_id_missing"


def test_oversized_request_is_rejected(tmp_path):
    worker, _ = make_worker(tmp_path)
    message = make_message(" " * 4097)
    result = worker(message)
    assert result["reason"] == "request_size_invalid"


def test_constructor_rejects_repository_outside_allowlisted_root(tmp_path):
    allowed = tmp_path / "allowed"
    outside = tmp_path / "outside"
    allowed.mkdir()
    outside.mkdir()
    with pytest.raises(ValueError, match="outside allowed_root"):
        RepositoryCartographerWorker(
            allowed_root=allowed,
            repositories={"escape": outside},
        )


def test_constructor_rejects_invalid_resource_limits(tmp_path):
    allowed = tmp_path / "allowed"
    repo = allowed / "repo"
    repo.mkdir(parents=True)
    with pytest.raises(ValueError):
        RepositoryCartographerWorker(allowed_root=allowed, repositories={"repo": repo}, max_entries=0)
    with pytest.raises(ValueError):
        RepositoryCartographerWorker(allowed_root=allowed, repositories={"repo": repo}, max_depth=21)
    with pytest.raises(ValueError):
        RepositoryCartographerWorker(allowed_root=allowed, repositories={"repo": repo}, sample_limit=101)


def test_inventory_is_bounded_by_configured_entry_limit(tmp_path):
    worker, repo = make_worker(tmp_path, max_entries=2, sample_limit=1)
    for index in range(10):
        (repo / f"file-{index}.txt").write_text("x", encoding="utf-8")
    result = worker(make_message(request()))
    assert result["status"] == "COMPLETED_READ_ONLY"
    assert result["counts"]["entries"] <= 2
    assert result["inventory_limit_reached"] is True
    assert len(result["sample"]) <= 1

def test_worker_runs_through_explicit_durable_message_dispatch(tmp_path):
    worker, _ = make_worker(tmp_path)
    bus = InternalMessageBus()
    runtime = WorkerRuntime(bus)
    runtime.register_handler(worker.agent_id, worker)
    message = make_message(request())
    bus.send(message)

    dispatch = runtime.dispatch_one(worker.agent_id)

    assert dispatch.status == "HANDLED"
    assert dispatch.result["status"] == "COMPLETED_READ_ONLY"
    receipt = bus.get_dispatch_result(message.message_id)
    assert receipt["status"] == "HANDLED"
    assert receipt["result"]["repository_id"] == "demo"
    assert bus.receive(worker.agent_id, unread_only=True) == []
    bus.close()
