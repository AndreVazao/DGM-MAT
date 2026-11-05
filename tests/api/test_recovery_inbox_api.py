from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.api import recovery_api
from core.api.security_policy import SecurityScope, classify_request_path
from core.recovery.recovery_ledger import RecoveryLedger


def _conversation(conversation_id="inbox-chat-1"):
    return {
        "id": conversation_id,
        "title": "Imported ChatGPT project discussion",
        "create_time": 1793520000,
        "mapping": {
            "user-node": {
                "parent": None,
                "children": [],
                "message": {
                    "author": {"role": "user"},
                    "content": {"parts": ["Keep the user request separate from the AI response."]},
                },
            },
            "assistant-node": {
                "parent": "user-node",
                "children": [],
                "message": {
                    "author": {"role": "assistant"},
                    "content": {"parts": ["The assistant response is stored separately."]},
                },
            },
        },
    }


def _client(monkeypatch, tmp_path):
    inbox = tmp_path / "conversation-imports"
    for provider in ("chatgpt", "gemini", "grok"):
        (inbox / provider).mkdir(parents=True)
    ledger = RecoveryLedger(tmp_path / "recovery.sqlite3")
    monkeypatch.setattr(recovery_api, "get_recovery_ledger", lambda: ledger)
    monkeypatch.setenv("DGM_CONVERSATION_IMPORT_DIR", str(inbox))
    app = FastAPI()
    app.include_router(recovery_api.router)
    return TestClient(app), ledger, inbox


def test_recovery_inbox_lists_metadata_only_and_classifies_provider_adapters(monkeypatch, tmp_path):
    client, _, inbox = _client(monkeypatch, tmp_path)
    (inbox / "chatgpt" / "conversations.json").write_text("[]", encoding="utf-8")
    (inbox / "gemini" / "takeout.zip").write_bytes(b"not imported")
    (inbox / "grok" / "account-export.json").write_text("{}", encoding="utf-8")

    response = client.get("/recovery/inbox")

    assert response.status_code == 200
    result = response.json()
    assert result["provider_content_read"] is False
    assert result["source_files_modified"] is False
    by_provider = {item["provider"]: item for item in result["providers"]}
    assert by_provider["chatgpt"]["files"][0]["status"] == "ready_to_import"
    assert by_provider["gemini"]["files"][0]["status"] == "awaiting_provider_adapter"
    assert by_provider["grok"]["files"][0]["status"] == "awaiting_provider_adapter"


def test_recovery_inbox_imports_chatgpt_but_preserves_unrecognized_provider_exports(monkeypatch, tmp_path):
    client, ledger, inbox = _client(monkeypatch, tmp_path)
    chatgpt_file = inbox / "chatgpt" / "conversations.json"
    chatgpt_file.write_text(json.dumps([_conversation()]), encoding="utf-8")
    gemini_file = inbox / "gemini" / "takeout.zip"
    gemini_file.write_bytes(b"unknown-gemini-schema")
    grok_file = inbox / "grok" / "account-export.json"
    grok_file.write_text('{"unknown":"schema"}', encoding="utf-8")

    first = client.post("/recovery/import/inbox")
    second = client.post("/recovery/import/inbox")

    assert first.status_code == second.status_code == 200
    assert first.json()["archived"] == 1
    assert first.json()["pending_provider_adapters"] == 2
    assert second.json()["skipped_existing"] == 1
    assert ledger.source_count() == 1
    assert chatgpt_file.is_file()
    assert gemini_file.read_bytes() == b"unknown-gemini-schema"
    assert grok_file.read_text(encoding="utf-8") == '{"unknown":"schema"}'


def test_recovery_inbox_routes_have_local_read_and_operator_import_scopes():
    read_route = classify_request_path("/recovery/inbox", "GET")
    import_route = classify_request_path("/recovery/import/inbox", "POST")
    assert read_route is not None and read_route.scope is SecurityScope.LOCAL_CLIENT
    assert import_route is not None and import_route.scope is SecurityScope.OPERATOR
    telescope_read = classify_request_path("/runtime/conversations/telescope/status", "GET")
    telescope_import = classify_request_path("/runtime/conversations/telescope/import", "POST")
    assert telescope_read is not None and telescope_read.scope is SecurityScope.LOCAL_CLIENT
    assert telescope_import is not None and telescope_import.scope is SecurityScope.OPERATOR
