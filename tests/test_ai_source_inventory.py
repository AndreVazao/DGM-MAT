from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from core.recovery.ai_source_inventory import (
    inventory_local_ai_sources,
    prepare_recovery_inbox,
    write_inventory_report,
)


def _history(profile: Path) -> None:
    profile.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(profile / "History")
    connection.execute(
        "CREATE TABLE urls (id INTEGER PRIMARY KEY, url LONGVARCHAR, title LONGVARCHAR, "
        "visit_count INTEGER DEFAULT 0, last_visit_time INTEGER DEFAULT 0)"
    )
    connection.executemany(
        "INSERT INTO urls(url,title,visit_count,last_visit_time) VALUES(?,?,?,?)",
        [
            ("https://chatgpt.com/c/chat-001", "DGM-MAT architecture", 4, 13400000000000000),
            ("https://chatgpt.com/g/project/c/chat-001", "DGM-MAT architecture", 2, 13400000001500000),
            ("https://grok.com/c/grok-001", "EVSE modular charger", 2, 13400000001000000),
            ("https://gemini.google.com/app/gem-001", "Virtual office research", 3, 13400000002000000),
            ("https://chatgpt.com/", "ChatGPT", 20, 13400000003000000),
            ("https://example.com/c/not-ai", "Not AI", 10, 13400000004000000),
        ],
    )
    connection.commit()
    connection.close()


def test_inventory_reads_only_provider_history_metadata_and_route_counts(tmp_path, monkeypatch):
    profile_root = tmp_path / "Chrome" / "User Data"
    profile = profile_root / "Default"
    _history(profile)
    (profile_root / "Crashpad").mkdir()
    indexeddb = profile / "IndexedDB"
    indexeddb.mkdir()
    (indexeddb / "https_chatgpt.com_0.indexeddb.leveldb").mkdir()
    (indexeddb / "https_grok.com_0.indexeddb.leveldb").mkdir()
    shortcuts = tmp_path / "Apps do Chrome"
    shortcuts.mkdir()
    for name in ("ChatGPT.lnk", "Grok.lnk", "Gemini.lnk"):
        (shortcuts / name).write_bytes(b"shortcut metadata")

    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "Local"))
    monkeypatch.setenv("APPDATA", str(tmp_path / "Roaming"))
    result = inventory_local_ai_sources(profile_root=profile_root, shortcuts_dir=shortcuts)

    assert result["complete_conversation_inventory"] is False
    assert result["conversation_content_read"] is False
    assert result["cookies_or_tokens_read"] is False
    item = result["profiles"][0]
    assert item["history"]["status"] == "read_only_snapshot"
    assert item["history"]["url_rows_by_provider"]["chatgpt"] == 3
    assert item["history"]["conversation_routes_by_provider"] == {
        "chatgpt": 1, "grok": 1, "gemini": 1
    }
    assert len(result["profiles"]) == 1
    assert item["history"]["conversation_entries"]["chatgpt"][0]["conversation_id"] == "chat-001"
    assert item["detected_providers"]["chatgpt"]["start_menu_shortcut"] is True
    assert item["detected_providers"]["gemini"]["start_menu_shortcut"] is True
    assert item["indexeddb_origin_names_only"] == [
        "https_chatgpt.com_0.indexeddb.leveldb",
        "https_grok.com_0.indexeddb.leveldb",
    ]


def test_inventory_marks_wal_as_incomplete_and_never_claims_full_history(tmp_path):
    profile_root = tmp_path / "User Data"
    profile = profile_root / "Default"
    _history(profile)
    (profile / "History-wal").write_bytes(b"pending wal")
    result = inventory_local_ai_sources(profile_root=profile_root, shortcuts_dir=tmp_path / "missing")
    history = result["profiles"][0]["history"]
    assert history["wal_present"] is True
    assert history["complete"] is False
    assert result["complete_conversation_inventory"] is False


def test_inbox_creation_preserves_existing_readme_and_files(tmp_path):
    root = tmp_path / "inbox"
    root.mkdir()
    readme = root / "README.md"
    readme.write_text("operator-owned instructions", encoding="utf-8")
    existing = root / "grok" / "export.zip"
    existing.parent.mkdir()
    existing.write_bytes(b"original archive")

    result = prepare_recovery_inbox(root)

    assert result["readme_created"] is False
    assert readme.read_text(encoding="utf-8") == "operator-owned instructions"
    assert existing.read_bytes() == b"original archive"
    assert (root / "chatgpt").is_dir()
    assert (root / "gemini").is_dir()
    assert (root / "_unknown").is_dir()


def test_report_write_is_atomic_and_json_serializable(tmp_path):
    destination = write_inventory_report({"safe": True}, tmp_path / "reports" / "inventory.json")
    assert destination.is_file()
    assert '"safe": true' in destination.read_text(encoding="utf-8")
    assert not destination.with_suffix(".json.tmp").exists()
