import json
from pathlib import Path

from core.conversation_intelligence.chrome_archive_importer import ChromeConversationArchiveImporter
from core.conversation_intelligence.pipeline import ConversationIntelligencePipeline
from core.vault import VaultCatalog


def test_importer_preserves_source_and_archives_full_messages(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("DGM_VAULT_PATH", str(tmp_path / "vault"))
    inbox = tmp_path / "Downloads" / "DGM-MAT-Conversation-Archive"
    archive = tmp_path / "archive"
    inbox.mkdir(parents=True)
    source = inbox / "capture-chatgpt-test.json"
    original = {
        "schema": "dgm-mat.chrome-conversation-capture.v1",
        "conversations": [{
            "id": "chatgpt-abc123",
            "provider": "chatgpt",
            "title": "DGM-MAT recovery",
            "url": "https://chatgpt.com/c/abc123",
            "content": "user: Keep the context.\n\nassistant: I will.",
            "completeness": "partial_dom_snapshot",
            "messages": [
                {"id": "u1", "role": "user", "content": "Keep the context.", "sequence": 0, "metadata": {"selector": "[data-message-author-role]"}},
                {"id": "a1", "role": "assistant", "content": "I will.", "sequence": 1},
            ],
        }],
    }
    source.write_text(json.dumps(original), encoding="utf-8")
    original_bytes = source.read_bytes()
    pipeline = ConversationIntelligencePipeline(
        progress_store_path=tmp_path / "progress.sqlite3"
    )
    importer = ChromeConversationArchiveImporter(inbox, archive, pipeline)

    result = importer.import_inbox()
    restored = pipeline.load_saved_audits("chatgpt")

    assert result["status"] == "completed"
    assert result["conversations_imported"] == 1
    assert result["messages_imported"] == 2
    assert source.read_bytes() == original_bytes
    assert Path(result["files"][0]["archive_path"]).is_file()
    assert [message.role for message in restored[0].conversation.messages] == ["user", "assistant"]
    assert restored[0].conversation.metadata["completeness"] == "partial_dom_snapshot"
    assert restored[0].conversation.messages[0].metadata["selector"] == "[data-message-author-role]"


def test_importer_is_idempotent_for_identical_downloads(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("DGM_VAULT_PATH", str(tmp_path / "vault"))
    inbox = tmp_path / "inbox"
    archive = tmp_path / "archive"
    inbox.mkdir()
    source = inbox / "inventory.json"
    source.write_text(json.dumps({
        "schema": "dgm-mat.chrome-conversation-inventory.v1",
        "items": [{
            "id": "grok-123",
            "provider": "grok",
            "title": "Grok conversation",
            "url": "https://grok.com/chat/123",
            "last_visit_at": "2026-11-06T10:00:00Z",
        }],
    }), encoding="utf-8")
    pipeline = ConversationIntelligencePipeline(progress_store_path=tmp_path / "progress.sqlite3")
    importer = ChromeConversationArchiveImporter(inbox, archive, pipeline)

    first = importer.import_inbox()
    second = importer.import_inbox()

    assert first["conversations_imported"] == 1
    assert second["conversations_imported"] == 1
    assert len(list(archive.glob("*.json"))) == 1
    assert len(pipeline.load_saved_audits("grok")) == 1


def test_importer_copies_raw_source_and_normalized_conversation_to_persistent_vault(tmp_path: Path):
    inbox = tmp_path / "Downloads" / "DGM-MAT-Conversation-Archive"
    inbox.mkdir(parents=True)
    source = inbox / "capture.json"
    source.write_text(json.dumps({
        "schema": "dgm-mat.chrome-conversation-capture.v1",
        "conversations": [{
            "id": "chatgpt-vault-1",
            "provider": "chatgpt",
            "title": "DGM-MAT vault integration",
            "url": "https://chatgpt.com/c/vault-1",
            "completeness": "partial_dom_snapshot",
            "messages": [{"id": "m1", "role": "user", "content": "Persist this transcript"}],
        }],
    }), encoding="utf-8")
    vault_root = tmp_path / "portable-vault"
    vault = VaultCatalog(vault_root)
    vault.register_project("dgm-mat", "DGM-MAT", aliases=["DGM-MAT"])
    pipeline = ConversationIntelligencePipeline(progress_store_path=tmp_path / "progress.sqlite3")
    importer = ChromeConversationArchiveImporter(
        inbox, pipeline=pipeline, vault_catalog=vault
    )

    result = importer.import_inbox()

    assert result["status"] == "completed"
    raw_copies = list((vault_root / "providers" / "chrome-imports").glob("*.json"))
    assert len(raw_copies) == 1
    assert json.loads(raw_copies[0].read_text(encoding="utf-8"))["schema"] == "dgm-mat.chrome-conversation-capture.v1"
    records = vault.list_conversations("dgm-mat")
    assert len(records) == 1
    assert records[0]["completeness"] == "partial_dom_snapshot"
    assert Path(records[0]["archive_path"]).is_file()


def _write_inventory(path: Path, conversation_id: str) -> None:
    path.write_text(json.dumps({
        "schema": "dgm-mat.chrome-conversation-inventory.v1",
        "items": [{"id": conversation_id, "provider": "grok", "title": conversation_id,
                   "url": f"https://grok.com/chat/{conversation_id}"}],
    }), encoding="utf-8")


def test_importer_reports_file_count_deferrals_without_reading_sources(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("DGM_VAULT_PATH", str(tmp_path / "vault"))
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    for index in range(ChromeConversationArchiveImporter.MAX_INBOX_FILES + 2):
        _write_inventory(inbox / f"{index:02d}.json", f"count-{index}")
    pipeline = ConversationIntelligencePipeline(progress_store_path=tmp_path / "progress.sqlite3")
    importer = ChromeConversationArchiveImporter(inbox, tmp_path / "archive", pipeline)
    result = importer.import_inbox()
    deferred = [item for item in result["files"] if item["status"] == "deferred_file_count_limit"]
    assert result["status"] == "partial"
    assert result["files_seen"] == ChromeConversationArchiveImporter.MAX_INBOX_FILES + 2
    assert result["files_deferred"] == 2
    assert result["files_processed"] == ChromeConversationArchiveImporter.MAX_INBOX_FILES
    assert [item["file"] for item in deferred] == ["10.json", "11.json"]
    assert all((inbox / item["file"]).is_file() for item in deferred)


def test_importer_reports_per_file_size_deferral(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("DGM_VAULT_PATH", str(tmp_path / "vault"))
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    oversized = inbox / "00-oversized.json"
    oversized.write_bytes(b" " * (ChromeConversationArchiveImporter.MAX_INBOX_FILE_BYTES + 1))
    _write_inventory(inbox / "01-valid.json", "valid-after-oversize")
    pipeline = ConversationIntelligencePipeline(progress_store_path=tmp_path / "progress.sqlite3")
    importer = ChromeConversationArchiveImporter(inbox, tmp_path / "archive", pipeline)
    result = importer.import_inbox()
    assert result["status"] == "partial"
    assert result["files_deferred"] == 1
    assert result["files"][0]["status"] == "deferred_file_size_limit"
    assert result["files_imported"] == 1


def test_importer_reports_total_size_deferral(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("DGM_VAULT_PATH", str(tmp_path / "vault"))
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    # Four files below the 4 MiB per-file cap exceed the 12 MiB aggregate cap.
    payload = json.dumps({"schema": "unsupported", "padding": "x" * (3 * 1024 * 1024)})
    for index in range(4):
        (inbox / f"{index:02d}-part.json").write_text(payload, encoding="utf-8")
    pipeline = ConversationIntelligencePipeline(progress_store_path=tmp_path / "progress.sqlite3")
    importer = ChromeConversationArchiveImporter(inbox, tmp_path / "archive", pipeline)
    result = importer.import_inbox()
    assert result["status"] == "partial"
    assert result["files_deferred"] == 1
    assert [item["status"] for item in result["files"]] == [
        "ignored_unsupported_schema", "ignored_unsupported_schema",
        "ignored_unsupported_schema", "deferred_total_size_limit",
    ]
