"""Operator API tests for importing local ChatGPT export files."""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.api import recovery_api
from core.api.security_policy import SecurityScope, classify_request_path
from core.recovery.recovery_ledger import RecoveryLedger


def _client(monkeypatch, tmp_path):
    ledger = RecoveryLedger(tmp_path / "ledger.sqlite3")
    monkeypatch.setattr(recovery_api, "get_recovery_ledger", lambda: ledger)
    monkeypatch.setenv("DGM_RECOVERY_ARCHIVE_ROOT", str(tmp_path / "archive"))
    app = FastAPI()
    app.include_router(recovery_api.router)
    return TestClient(app), ledger


def _conversation(conversation_id="conversation-1"):
    return {
        "id": conversation_id,
        "title": "DGM-MAT recovery test",
        "mapping": {
            "node-user": {
                "parent": None,
                "children": [],
                "message": {
                    "author": {"role": "user"},
                    "content": {"parts": ["Preserve this conversation"]},
                },
            }
        },
    }


def test_chatgpt_import_route_is_operator_only():
    route = classify_request_path("/recovery/import/chatgpt", "POST")
    assert route is not None
    assert route.scope is SecurityScope.OPERATOR


def test_json_upload_archives_export_and_reports_truthful_provenance(monkeypatch, tmp_path):
    client, ledger = _client(monkeypatch, tmp_path)
    payload = json.dumps([_conversation()], ensure_ascii=False).encode("utf-8")

    response = client.post("/recovery/import/chatgpt?format=json", content=payload)

    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "completed"
    assert result["provider"] == "chatgpt"
    assert result["discovered"] == 1
    assert result["archived"] == 1
    assert result["source_modified"] is False
    assert result["provider_access_used"] is False
    assert result["provider_deletion_attempted"] is False
    saved = ledger.get("chatgpt", "conversation-1")
    assert saved is not None
    assert saved.original_location == "api-upload"
    assert result["source_file"] == "uploaded-request-body"
    assert Path(saved.raw_archive_path).is_file()
    assert ledger.source_count() == 1


def test_json_upload_is_idempotent_on_repeated_request(monkeypatch, tmp_path):
    client, ledger = _client(monkeypatch, tmp_path)
    payload = json.dumps([_conversation()], ensure_ascii=False).encode("utf-8")

    first = client.post("/recovery/import/chatgpt?format=json", content=payload)
    second = client.post("/recovery/import/chatgpt?format=json", content=payload)

    assert first.status_code == second.status_code == 200
    assert first.json()["archived"] == 1
    assert second.json()["skipped_existing"] == 1
    assert ledger.source_count() == 1


def test_zip_upload_does_not_extract_untrusted_paths(monkeypatch, tmp_path):
    client, ledger = _client(monkeypatch, tmp_path)
    source = tmp_path / "source.zip"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("conversations.json", json.dumps([_conversation("zip-1")]))
        archive.writestr("../../outside.txt", "must not be extracted")
    payload = source.read_bytes()

    response = client.post("/recovery/import/chatgpt?format=zip", content=payload)

    assert response.status_code == 200
    assert response.json()["archived"] == 1
    saved = ledger.get("chatgpt", "zip-1")
    assert saved is not None
    assert saved.original_location == "api-upload"
    assert not (tmp_path / "outside.txt").exists()


def test_upload_rejects_empty_invalid_format_and_oversized_body(monkeypatch, tmp_path):
    client, _ = _client(monkeypatch, tmp_path)

    assert client.post("/recovery/import/chatgpt?format=json", content=b"").status_code == 400
    assert client.post("/recovery/import/chatgpt?format=exe", content=b"x").status_code == 400
    assert client.post("/recovery/import/chatgpt?format=json", content=b"not-json").status_code == 400

    monkeypatch.setattr(recovery_api, "MAX_CHATGPT_UPLOAD_BYTES", 8)
    response = client.post("/recovery/import/chatgpt?format=json", content=b"0123456789")
    assert response.status_code == 413
