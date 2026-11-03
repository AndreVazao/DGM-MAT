from __future__ import annotations

import json
import subprocess

from core.conversation_intelligence.telescope_adapter import TelescopeAdapter


def test_sessions_projects_only_allowlisted_metadata(monkeypatch):
    payload = [{
        "session_id": "session-1",
        "agent_id": "claude-code",
        "cwd": r"C:\Users\private-user\Projects\DGM-MAT",
        "git_branch": "main",
        "status": "completed",
        "started_at": "2026-11-03T10:00:00Z",
        "turn_count": 8,
        "last_message": "PRIVATE PROMPT PREVIEW",
        "turns": [{"content": "PRIVATE FULL TRANSCRIPT"}],
        "metadata": {"api_key": "PRIVATE SECRET"},
        "git_repo": "https://user:token@example.invalid/private.git",
    }]
    monkeypatch.setattr("shutil.which", lambda _: "tele.exe")
    monkeypatch.setattr(
        "subprocess.run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, json.dumps(payload), ""),
    )

    sessions = TelescopeAdapter().sessions()

    assert sessions == [{
        "session_id": "session-1",
        "agent_id": "claude-code",
        "git_branch": "main",
        "status": "completed",
        "started_at": "2026-11-03T10:00:00Z",
        "turn_count": 8,
        "project": "DGM-MAT",
    }]
    serialized = json.dumps(sessions)
    assert "PRIVATE" not in serialized
    assert "private-user" not in serialized
    assert "api_key" not in serialized
    assert "token@" not in serialized


def test_conversation_is_metadata_only_and_never_contains_turns(monkeypatch):
    payload = {
        "session_id": "session-2",
        "agent_id": "copilot",
        "cwd": r"C:\Users\private-user\Projects\EVSE",
        "git_branch": "feature/test",
        "status": "completed",
        "turn_count": 3,
        "last_message": "PRIVATE LAST MESSAGE",
        "turns": [{"role": "user", "content": "PRIVATE TURN BODY"}],
        "metadata": {"access_token": "PRIVATE TOKEN"},
    }
    monkeypatch.setattr("shutil.which", lambda _: "tele.exe")
    monkeypatch.setattr(
        "subprocess.run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, json.dumps(payload), ""),
    )

    record = TelescopeAdapter().conversation("session-2")

    assert record is not None
    assert record.conversation_id == "session-2"
    assert record.source == "telescope-metadata"
    assert record.metadata["content_policy"] == "metadata_only"
    serialized = record.content + json.dumps(record.metadata)
    assert "PRIVATE" not in serialized
    assert "private-user" not in serialized
    assert "access_token" not in serialized
    assert "turns" not in serialized


def test_invalid_session_id_is_rejected_without_running_cli(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: "tele.exe")
    monkeypatch.setattr(
        "subprocess.run",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("CLI must not run")),
    )

    assert TelescopeAdapter().conversation(" " ) is None
    assert TelescopeAdapter().conversation("x" * 257) is None


def test_cli_timeout_returns_empty_metadata(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: "tele.exe")
    monkeypatch.setattr(
        "subprocess.run",
        lambda *args, **kwargs: (_ for _ in ()).throw(subprocess.TimeoutExpired("tele", 15)),
    )

    assert TelescopeAdapter().sessions() == []
    assert TelescopeAdapter().conversation("session-3") is None
