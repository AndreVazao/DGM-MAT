from __future__ import annotations

import json

from core.organization.models import Message
from core.organization.python_test_inventory_worker import PythonTestInventoryWorker


def make_worker(tmp_path, **kwargs):
    allowed = tmp_path / "workspace"
    repo = allowed / "demo"
    tests = repo / "tests" / "unit"
    tests.mkdir(parents=True)
    (tests / "test_service.py").write_text(
        "import pytest\n\n@pytest.fixture\ndef client():\n    return object()\n\n"
        "@pytest.mark.parametrize('value', [1, 2])\ndef test_value(value):\n    assert value\n",
        encoding="utf-8",
    )
    (tests / "test_async.py").write_text(
        "import unittest\n\nasync def test_async_case():\n    return True\n\n"
        "class TestGroup:\n    def test_member(self):\n        return True\n",
        encoding="utf-8",
    )
    (repo / "src").mkdir()
    (repo / "src" / "service.py").write_text("def run(): return True", encoding="utf-8")
    hidden = repo / ".venv" / "tests"
    hidden.mkdir(parents=True)
    (hidden / "test_hidden.py").write_text("def test_secret(): pass", encoding="utf-8")
    return PythonTestInventoryWorker(allowed_root=allowed, repositories={"demo": repo}, **kwargs), repo


def make_message(body, *, sender="agent:hq-orchestrator", recipient=PythonTestInventoryWorker.agent_id,
                 mission="mission:test-inventory", correlation="corr:test-inventory"):
    return Message(sender_id=sender, recipient_id=recipient, subject="Inventory Python tests",
                   body=body, mission_id=mission, correlation_id=correlation)


def request(repository_id="demo"):
    return json.dumps({"schema_version": 1, "operation": "inventory_python_tests",
                       "repository_id": repository_id})


def test_inventories_test_structure_without_execution_or_source_disclosure(tmp_path):
    worker, repo = make_worker(tmp_path)
    before = {p.relative_to(repo).as_posix(): p.read_bytes() for p in repo.rglob("*") if p.is_file()}
    result = worker(make_message(request()))
    assert result["status"] == "COMPLETED_READ_ONLY"
    assert result["test_files_discovered"] == 2
    assert result["test_files_analyzed"] == 2
    assert result["test_functions"] == 3
    assert result["async_test_functions"] == 1
    assert result["test_classes"] == 1
    assert result["fixtures"] == 1
    assert result["parametrize_decorators"] == 1
    assert result["framework_imports"] == ["pytest", "unittest"]
    assert "def test_value" not in json.dumps(result)
    assert result["tests_executed"] is False
    assert result["code_executed"] is False
    after = {p.relative_to(repo).as_posix(): p.read_bytes() for p in repo.rglob("*") if p.is_file()}
    assert after == before


def test_invalid_requests_fail_closed(tmp_path):
    worker, _ = make_worker(tmp_path)
    assert worker(make_message("not-json"))["reason"] == "request_json_invalid"
    bad = json.dumps({"schema_version": 1, "operation": "run_tests", "repository_id": "demo"})
    assert worker(make_message(bad))["reason"] == "operation_not_allowed"
    unknown = json.dumps({"schema_version": 1, "operation": "inventory_python_tests", "repository_id": "other"})
    assert worker(make_message(unknown))["reason"] == "repository_not_allowlisted"


def test_message_identity_is_enforced(tmp_path):
    worker, _ = make_worker(tmp_path)
    assert worker(make_message(request(), sender="agent:intruder"))["reason"] == "sender_not_allowlisted"
    assert worker(make_message(request(), recipient="agent:other"))["reason"] == "recipient_mismatch"
    assert worker(make_message(request(), mission=None))["reason"] == "mission_or_correlation_id_missing"


def test_file_limit_is_enforced(tmp_path):
    worker, _ = make_worker(tmp_path, max_files=1)
    assert worker(make_message(request()))["reason"] == "file_limit_exceeded"
