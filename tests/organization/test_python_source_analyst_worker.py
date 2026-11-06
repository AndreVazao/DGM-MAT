from __future__ import annotations

import json

import pytest

from core.organization.models import Message
from core.organization.python_source_analyst_worker import PythonSourceAnalystWorker


def make_worker(tmp_path, **kwargs):
    allowed = tmp_path / "workspace"
    repo = allowed / "demo"
    repo.mkdir(parents=True)
    (repo / "app.py").write_text("import os\n\nclass Service:\n    def run(self):\n        return 1\n", encoding="utf-8")
    (repo / "broken.py").write_text("def broken(:\n", encoding="utf-8")
    (repo / ".env").write_text("SECRET_VALUE", encoding="utf-8")
    hidden = repo / ".git"
    hidden.mkdir()
    (hidden / "hidden.py").write_text("raise RuntimeError('must not be read')", encoding="utf-8")
    return PythonSourceAnalystWorker(allowed_root=allowed, repositories={"demo": repo}, **kwargs), repo


def make_message(body, *, sender="agent:hq-orchestrator", recipient=PythonSourceAnalystWorker.agent_id,
                 mission="mission:python-analysis", correlation="corr:python-analysis"):
    return Message(sender_id=sender, recipient_id=recipient, subject="Analyze Python source",
                   body=body, mission_id=mission, correlation_id=correlation)


def request(repository_id="demo"):
    return json.dumps({"schema_version": 1, "operation": "analyze_python_repository",
                       "repository_id": repository_id})


def test_analyzes_ast_without_returning_source_or_mutating_files(tmp_path):
    worker, repo = make_worker(tmp_path)
    before = {p.relative_to(repo).as_posix(): p.read_bytes() for p in repo.rglob("*") if p.is_file()}
    result = worker(make_message(request()))
    assert result["status"] == "COMPLETED_READ_ONLY"
    assert result["files_discovered"] == 2
    assert result["files_analyzed"] == 2
    assert result["syntax_error_files"] == 1
    assert result["definitions"]["classes"] == 1
    assert result["definitions"]["functions"] == 1
    assert result["imports"] == ["os"]
    assert "SECRET_VALUE" not in json.dumps(result)
    assert "must not be read" not in json.dumps(result)
    assert result["code_executed"] is False
    assert result["files_modified"] is False
    after = {p.relative_to(repo).as_posix(): p.read_bytes() for p in repo.rglob("*") if p.is_file()}
    assert after == before


@pytest.mark.parametrize(("body", "reason"), [
    ("not-json", "request_json_invalid"),
    ("{}", "request_schema_invalid"),
    (json.dumps({"schema_version": 2, "operation": "analyze_python_repository", "repository_id": "demo"}),
     "request_schema_version_unsupported"),
    (json.dumps({"schema_version": 1, "operation": "shell", "repository_id": "demo"}),
     "operation_not_allowed"),
    (request("../outside"), "repository_id_invalid"),
    (request("unknown"), "repository_not_allowlisted"),
])
def test_invalid_requests_fail_closed(tmp_path, body, reason):
    worker, _ = make_worker(tmp_path)
    result = worker(make_message(body))
    assert result["status"] == "BLOCKED"
    assert result["reason"] == reason


def test_sender_recipient_mission_and_correlation_are_checked(tmp_path):
    worker, _ = make_worker(tmp_path)
    assert worker(make_message(request(), sender="agent:intruder"))["reason"] == "sender_not_allowlisted"
    assert worker(make_message(request(), recipient="agent:other"))["reason"] == "recipient_mismatch"
    assert worker(make_message(request(), mission=None))["reason"] == "mission_or_correlation_id_missing"
    assert worker(make_message(request(), correlation=None))["reason"] == "mission_or_correlation_id_missing"


def test_resource_limits_are_validated_and_enforced(tmp_path):
    worker, _ = make_worker(tmp_path, max_files=1)
    assert worker(make_message(request()))["reason"] == "file_limit_exceeded"
    with pytest.raises(ValueError):
        make_worker(tmp_path / "other", max_files=0)


def test_constructor_rejects_repository_outside_allowed_root(tmp_path):
    allowed, outside = tmp_path / "allowed", tmp_path / "outside"
    allowed.mkdir()
    outside.mkdir()
    with pytest.raises(ValueError):
        PythonSourceAnalystWorker(allowed_root=allowed, repositories={"escape": outside})
