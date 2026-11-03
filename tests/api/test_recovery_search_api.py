"""End-to-end tests for bounded recovery search and transcript reads."""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.api import recovery_api
from core.api.security_policy import SecurityScope, classify_request_path
from core.recovery.chatgpt_export_importer import import_chatgpt_conversations_json
from core.recovery.recovery_ledger import RecoveryLedger


def _conversation():
    return {
        "id": "recovery-search-001",
        "title": "DGM-MAT brain integration",
        "create_time": 1791000000,
        "mapping": {
            "user-node": {
                "parent": None,
                "children": ["assistant-node"],
                "message": {
                    "author": {"role": "user"},
                    "create_time": 1791000001,
                    "content": {"content_type": "text", "parts": ["Find the distinctive phrase cobalt lighthouse in the recovered archive."]},
                },
            },
            "assistant-node": {
                "parent": "user-node",
                "children": [],
                "message": {
                    "author": {"role": "assistant"},
                    "create_time": 1791000002,
                    "content": {"content_type": "text", "parts": ["Confirmed: the cobalt lighthouse is the recovery test marker."]},
                },
            },
        },
    }


def _client(monkeypatch, tmp_path):
    archive_root = tmp_path / "archive"
    ledger = RecoveryLedger(tmp_path / "ledger.sqlite3")
    source_file = tmp_path / "conversations.json"
    source_file.write_text(json.dumps([_conversation()]), encoding="utf-8")
    report = import_chatgpt_conversations_json(source_file, archive_root, ledger)
    assert report.archived == 1
    monkeypatch.setenv("DGM_RECOVERY_ARCHIVE_ROOT", str(archive_root))
    monkeypatch.setattr(recovery_api, "get_recovery_ledger", lambda: ledger)
    app = FastAPI()
    app.include_router(recovery_api.router)
    return TestClient(app), ledger, archive_root


def test_recovery_search_and_message_read_are_operator_only():
    assert classify_request_path("/recovery/search", "GET").scope is SecurityScope.OPERATOR
    assert classify_request_path(
        "/recovery/sources/chatgpt/recovery-search-001/messages", "GET"
    ).scope is SecurityScope.OPERATOR


def test_search_finds_message_body_and_returns_grounded_snippet(monkeypatch, tmp_path):
    client, _, _ = _client(monkeypatch, tmp_path)
    response = client.get("/recovery/search", params={"q": "cobalt lighthouse"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["result_count"] == 1
    assert payload["results"][0]["source_id"] == "recovery-search-001"
    assert payload["results"][0]["match_type"] == "message"
    assert "cobalt lighthouse" in payload["results"][0]["snippet"].casefold()
    assert payload["provider_access_used"] is False
    assert payload["source_modified"] is False


def test_read_messages_is_paginated_and_returns_original_message_content(monkeypatch, tmp_path):
    client, _, _ = _client(monkeypatch, tmp_path)
    first = client.get(
        "/recovery/sources/chatgpt/recovery-search-001/messages",
        params={"limit": 1, "offset": 0},
    )
    second = client.get(
        "/recovery/sources/chatgpt/recovery-search-001/messages",
        params={"limit": 1, "offset": 1},
    )

    assert first.status_code == second.status_code == 200
    assert first.json()["total_messages"] == 2
    assert first.json()["items"][0]["role"] == "user"
    assert second.json()["items"][0]["role"] == "assistant"
    assert "cobalt lighthouse" in str(first.json()["items"][0]["content"]).casefold()
    assert first.json()["archive_sha256_verified"] is True


def test_message_read_rejects_modified_archive(monkeypatch, tmp_path):
    client, ledger, _ = _client(monkeypatch, tmp_path)
    source = ledger.get("chatgpt", "recovery-search-001")
    Path(source.raw_archive_path).write_text("tampered", encoding="utf-8")

    response = client.get("/recovery/sources/chatgpt/recovery-search-001/messages")

    assert response.status_code == 409


def test_search_rejects_too_short_query(monkeypatch, tmp_path):
    client, _, _ = _client(monkeypatch, tmp_path)
    response = client.get("/recovery/search", params={"q": " "})
    assert response.status_code == 422


def test_message_read_does_not_allow_archive_path_escape(monkeypatch, tmp_path):
    client, ledger, _ = _client(monkeypatch, tmp_path)
    from core.recovery.recovery_ledger import RecoverySource
    ledger.register(RecoverySource(
        provider="chatgpt",
        source_id="outside-path",
        title="Outside path",
        source_date="2026-11-03",
        raw_archive_path=str(tmp_path / "outside.conversation.json"),
    ))

    response = client.get("/recovery/sources/chatgpt/outside-path/messages")

    assert response.status_code == 404
