"""Tests for safe ChatGPT export ingestion."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from core.recovery.chatgpt_export_importer import (
    ChatGPTExportError,
    import_chatgpt_conversations_json,
)
from core.recovery.recovery_ledger import RecoveryLedger


def write_export(path: Path, records: list[dict]) -> bytes:
    raw = json.dumps(records, ensure_ascii=False, indent=2).encode("utf-8")
    path.write_bytes(raw)
    return raw


def test_import_archives_messages_and_leaves_original_unchanged(tmp_path):
    source = tmp_path / "conversations.json"
    original = write_export(source, [{
        "id": "conversation-1",
        "title": "DGM-MAT discussion",
        "create_time": 1792600000,
        "mapping": {
            "node-user": {
                "parent": None,
                "children": ["node-assistant"],
                "message": {
                    "author": {"role": "user"},
                    "create_time": 1792600001,
                    "content": {"parts": ["Build recovery first"]},
                },
            },
            "node-assistant": {
                "parent": "node-user",
                "children": [],
                "message": {
                    "author": {"role": "assistant"},
                    "create_time": 1792600002,
                    "content": {"parts": ["Agreed"]},
                },
            },
        },
    }])
    ledger = RecoveryLedger(tmp_path / "ledger.sqlite3")

    report = import_chatgpt_conversations_json(source, tmp_path / "archive", ledger)

    assert report.discovered == 1
    assert report.archived == 1
    assert report.partial == 0
    assert report.failed == 0
    assert source.read_bytes() == original
    saved = ledger.get("chatgpt", "conversation-1")
    assert saved is not None
    assert saved.capture_status == "captured"
    assert saved.completeness == "unknown"
    assert saved.deletion_status == "not_eligible"
    assert RecoveryLedger.sha256_file(saved.raw_archive_path) == saved.raw_sha256
    messages_path = Path(saved.raw_archive_path).with_name("conversation-1.messages.jsonl")
    messages = [json.loads(line) for line in messages_path.read_text(encoding="utf-8").splitlines()]
    assert [item["role"] for item in messages] == ["user", "assistant"]
    assert messages[0]["message"]["content"]["parts"] == ["Build recovery first"]


def test_import_is_idempotent_for_verified_existing_archive(tmp_path):
    source = tmp_path / "conversations.json"
    write_export(source, [{"id": "same-id", "title": "One", "mapping": {"n": {"message": {"author": {"role": "user"}}}}}])
    ledger = RecoveryLedger(tmp_path / "ledger.sqlite3")

    first = import_chatgpt_conversations_json(source, tmp_path / "archive", ledger)
    second = import_chatgpt_conversations_json(source, tmp_path / "archive", ledger)

    assert first.archived == 1
    assert second.skipped_existing == 1
    assert second.archived == 0
    assert ledger.source_count() == 1


def test_attachment_reference_is_partial_and_never_deletion_eligible(tmp_path):
    source = tmp_path / "conversations.json"
    write_export(source, [{
        "id": "with-file",
        "title": "Attachment",
        "mapping": {"n": {"message": {
            "author": {"role": "user"},
            "content": {"parts": ["See file"]},
            "metadata": {"attachments": [{"id": "file-1"}]},
        }}},
    }])
    ledger = RecoveryLedger(tmp_path / "ledger.sqlite3")

    report = import_chatgpt_conversations_json(source, tmp_path / "archive", ledger)
    saved = ledger.get("chatgpt", "with-file")

    assert report.partial == 1
    assert saved.capture_status == "partial"
    assert saved.completeness == "partial"
    assert saved.deletion_status == "not_eligible"
    assert "attachment files not copied" in saved.last_error


def test_conflicting_archive_is_never_overwritten(tmp_path):
    source = tmp_path / "conversations.json"
    write_export(source, [{"id": "stable-id", "title": "First", "mapping": {"n": {"message": {"author": {"role": "user"}}}}}])
    ledger = RecoveryLedger(tmp_path / "ledger.sqlite3")
    import_chatgpt_conversations_json(source, tmp_path / "archive", ledger)
    saved = ledger.get("chatgpt", "stable-id")
    original_archive = Path(saved.raw_archive_path).read_bytes()

    changed = write_export(source, [{"id": "stable-id", "title": "Changed", "mapping": {"n": {"message": {"author": {"role": "assistant"}}}}}])
    report = import_chatgpt_conversations_json(source, tmp_path / "archive", ledger)

    assert report.failed == 1
    assert Path(saved.raw_archive_path).read_bytes() == original_archive
    assert source.read_bytes() == changed


def test_malformed_export_is_rejected_without_archive_writes(tmp_path):
    source = tmp_path / "conversations.json"
    source.write_text('[{"id":"broken"}', encoding="utf-8")
    ledger = RecoveryLedger(tmp_path / "ledger.sqlite3")

    with pytest.raises(ChatGPTExportError):
        import_chatgpt_conversations_json(source, tmp_path / "archive", ledger)

    assert ledger.source_count() == 0


def test_non_object_records_are_reported_and_skipped(tmp_path):
    source = tmp_path / "conversations.json"
    write_export(source, [None, {"id": "valid", "title": "Valid", "mapping": {"n": {"message": {"author": {"role": "user"}}}}}])
    ledger = RecoveryLedger(tmp_path / "ledger.sqlite3")

    report = import_chatgpt_conversations_json(source, tmp_path / "archive", ledger)

    assert report.discovered == 2
    assert report.archived == 1
    assert report.failed == 1
    assert ledger.source_count() == 1
