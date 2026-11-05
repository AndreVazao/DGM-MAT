from __future__ import annotations

import json
from pathlib import Path

from core.conversation_intelligence.telescope_archive_importer import (
    TelescopeArchiveImporter,
    redact_conversation_text,
)


class FakePipeline:
    def __init__(self):
        self.calls = []

    def ingest_file(self, path, provider):
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        self.calls.append({"path": str(path), "provider": provider, "payload": payload})
        return [object() for _ in payload]


def _payload():
    sessions = [{
        "session_id": "session-001",
        "agent_id": "agent-claude",
        "cwd": r"C:\Projects\DemoProject",
        "git_branch": "main",
        "started_at": "2026-11-01T10:00:00Z",
        "ended_at": "2026-11-01T10:05:00Z",
        "status": "completed",
        "last_message": "MUST_NOT_BE_IMPORTED",
        "opaque_metadata": {"cookie": "MUST_NOT_BE_IMPORTED"},
    }]
    agents = [{"agent_id": "agent-claude", "name": "Claude Code"}]
    turns = [
        {
            "session_id": "session-001",
            "turn_id": "turn-001",
            "turn_index": 1,
            "started_at": "2026-11-01T10:00:00Z",
            "ended_at": "2026-11-01T10:02:00Z",
            "user_message": "Build the demo and use api_key=super-secret-value",
            "assistant_response": "I will inspect the project. Bearer abcdef1234567890",
        },
        {
            "session_id": "session-001",
            "turn_id": "turn-002",
            "turn_index": 2,
            "started_at": "2026-11-01T10:03:00Z",
            "ended_at": "2026-11-01T10:05:00Z",
            "user_message": "Please keep going.",
            "assistant_response": "",
        },
    ]
    repositories = [{
        "path": r"C:\Projects\DemoProject",
        "name": "demo-repo",
        "project_group": "DemoProject",
        "project_group_basis": "shared_parent_folder",
    }]
    return sessions, turns, agents, repositories


def test_telescope_archive_import_preserves_roles_and_redacts_secrets(tmp_path):
    pipeline = FakePipeline()
    importer = TelescopeArchiveImporter(
        archive_root=tmp_path / "archive",
        executable="tele",
        pipeline=pipeline,
    )
    sessions, turns, agents, repositories = _payload()

    result = importer.import_payload(sessions, turns, agents, repositories)

    assert result["status"] == "complete"
    assert result["discovered_sessions"] == 1
    assert result["imported_sessions"] == 1
    assert result["turns"] == 2
    assert result["user_messages"] == 2
    assert result["assistant_messages"] == 1
    assert result["missing_assistant_responses"] == 1
    assert result["pipeline_audits"] == 1

    archive = next((tmp_path / "archive" / "claude-code").glob("*.md"))
    text = archive.read_text(encoding="utf-8")
    assert "### UTILIZADOR" in text
    assert "### CLAUDE CODE" in text
    assert "Build the demo" in text
    assert "I will inspect the project" in text
    assert "[Resposta da IA não capturada" in text
    assert "super-secret-value" not in text
    assert "abcdef1234567890" not in text
    assert "MUST_NOT_BE_IMPORTED" not in text
    assert "C:\\Projects\\DemoProject" not in text
    assert "DemoProject" in text

    normalized = pipeline.calls[0]["payload"][0]
    assert [message["role"] for message in normalized["messages"]] == [
        "user", "assistant", "user"
    ]
    assert normalized["provider"] == "claude"
    assert pipeline.calls[0]["provider"] == "claude"


def test_telescope_archive_import_is_idempotent_and_keeps_old_manifest_entries(tmp_path):
    pipeline = FakePipeline()
    importer = TelescopeArchiveImporter(
        archive_root=tmp_path / "archive",
        executable="tele",
        pipeline=pipeline,
    )
    sessions, turns, agents, repositories = _payload()
    first = importer.import_payload(sessions, turns, agents, repositories)
    second = importer.import_payload(sessions, turns, agents, repositories)

    assert first["updated_sessions"] == 1
    assert second["updated_sessions"] == 0
    assert second["unchanged_sessions"] == 1
    assert importer.get_status()["imported_sessions"] == 1


def test_telescope_archive_project_mapping_requires_a_known_repository(tmp_path):
    pipeline = FakePipeline()
    importer = TelescopeArchiveImporter(
        archive_root=tmp_path / "archive",
        executable="tele",
        pipeline=pipeline,
    )
    sessions, turns, agents, _ = _payload()
    result = importer.import_payload(sessions, turns, agents, repositories=[])

    assert result["imported_sessions"] == 1
    archive = next((tmp_path / "archive" / "claude-code").glob("*.md"))
    text = archive.read_text(encoding="utf-8")
    assert "DemoProject" in text
    assert "C:\\Projects\\DemoProject" not in text


def test_telescope_secret_redaction_covers_private_keys_and_provider_tokens():
    value = (
        "token=secret-value ghp_abcdefghijklmnopqrstuvwxyz123456 "
        "sk-abcdefghijklmnopqrstuvwxyz123456 "
        "-----BEGIN RSA PRIVATE KEY-----\nPRIVATE\n-----END RSA PRIVATE KEY-----"
    )
    redacted = redact_conversation_text(value)

    assert "secret-value" not in redacted
    assert "ghp_abcdefghijklmnopqrstuvwxyz123456" not in redacted
    assert "sk-abcdefghijklmnopqrstuvwxyz123456" not in redacted
    assert "-----BEGIN RSA PRIVATE KEY-----" not in redacted
    assert "-----END RSA PRIVATE KEY-----" not in redacted


def test_telescope_archive_does_not_treat_user_profile_root_as_a_project(tmp_path):
    pipeline = FakePipeline()
    importer = TelescopeArchiveImporter(
        archive_root=tmp_path / "archive",
        executable="tele",
        pipeline=pipeline,
    )
    sessions, turns, agents, _ = _payload()
    sessions[0]["cwd"] = str(Path.home())
    result = importer.import_payload(sessions, turns, agents, repositories=[])

    assert result["imported_sessions"] == 1
    normalized = pipeline.calls[0]["payload"][0]
    assert normalized["metadata"]["project"] is None
    assert normalized["metadata"]["project_group_basis"] == "unassigned_cwd"
    assert normalized["metadata"]["project_group_confidence"] == 0.0
