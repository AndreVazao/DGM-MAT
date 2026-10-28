from argparse import Namespace
from pathlib import Path

import pytest

from scripts import diagnose_live_mission as diagnostic


def test_validate_base_url_only_accepts_loopback_http():
    assert diagnostic.validate_base_url("http://127.0.0.1:8181/") == "http://127.0.0.1:8181"
    assert diagnostic.validate_base_url("http://localhost:8181") == "http://localhost:8181"
    assert diagnostic.validate_base_url("http://[::1]:8181") == "http://[::1]:8181"
    for value in (
        "https://127.0.0.1:8181",
        "http://192.168.1.10:8181",
        "http://user:password@127.0.0.1:8181",
        "http://127.0.0.1:8181/path",
    ):
        with pytest.raises(ValueError):
            diagnostic.validate_base_url(value)


def test_live_diagnostic_reports_real_terminal_result_without_persisting_tokens(monkeypatch, tmp_path: Path):
    bootstrap_file = tmp_path / "bootstrap.token"
    bootstrap_file.write_text("BOOTSTRAP_SECRET_" + ("x" * 64), encoding="utf-8")
    monkeypatch.setattr(diagnostic, "bootstrap_path", lambda: bootstrap_file)

    calls = []
    def fake_request(base_url, path, *, method="GET", payload=None, bearer=None, timeout=5.0):
        calls.append((path, method, payload, bearer))
        if path == "/health":
            return 200, {"status": "healthy", "service": "dgm-mat"}
        if path == "/auth/session":
            assert bearer == bootstrap_file.read_text(encoding="utf-8")
            return 201, {
                "access_token": "SESSION_SECRET_DO_NOT_PERSIST",
                "token_type": "Bearer",
                "scopes": ["local-client", "operator"],
            }
        if path == "/runtime/health":
            assert bearer == "SESSION_SECRET_DO_NOT_PERSIST"
            return 200, {"status": "running"}
        if path == "/runtime/missions" and method == "POST":
            assert payload["goal"] == "Lista os repositórios locais"
            return 200, {
                "status": "success",
                "mission_id": "mission_1234abcd",
                "mission_status": "QUEUED",
                "action_id": 123,
                "action_status": "APPROVED",
            }
        if path == "/runtime/missions/mission_1234abcd":
            assert bearer == "SESSION_SECRET_DO_NOT_PERSIST"
            return 200, {
                "mission_id": "mission_1234abcd",
                "status": "COMPLETED",
                "handler": "list_repositories",
                "result": {"status": "success", "handler": "list_repositories"},
                "output": "Found 3 repositories",
                "error": None,
            }
        raise AssertionError(f"Unexpected request: {method} {path}")

    monkeypatch.setattr(diagnostic, "request_json", fake_request)
    args = Namespace(
        base_url="http://127.0.0.1:8181",
        request_timeout=2,
        poll_timeout=5,
        poll_interval=0.5,
    )
    exit_code, report = diagnostic.run(args)

    serialized = __import__("json").dumps(report)
    assert exit_code == 0
    assert report["overall"] == "PASS"
    assert report["mission"]["last_checkpoint"]["status"] == "COMPLETED"
    assert "BOOTSTRAP_SECRET_" not in serialized
    assert "SESSION_SECRET_DO_NOT_PERSIST" not in serialized
    assert sum(1 for path, method, *_ in calls if path == "/runtime/missions" and method == "POST") == 1
