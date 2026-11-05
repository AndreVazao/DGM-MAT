from __future__ import annotations

import hashlib
import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.api import browser_capture_api
from core.api.security_policy import SecurityScope, classify_request_path
from core.recovery.recovery_ledger import RecoveryLedger


def _client(monkeypatch, tmp_path):
    ledger = RecoveryLedger(tmp_path / "ledger.sqlite3")
    monkeypatch.setattr(browser_capture_api, "_ledger", lambda: ledger)
    monkeypatch.setenv("DGM_RECOVERY_ARCHIVE_ROOT", str(tmp_path / "archive"))
    app = FastAPI()
    app.include_router(browser_capture_api.router)
    return TestClient(app), ledger


def _discovery(provider="chatgpt", source_id="conversation-1", url=None):
    if url is None:
        url = {
            "chatgpt": "https://chatgpt.com/c/conversation-1",
            "gemini": "https://gemini.google.com/app/conversation-1",
            "grok": "https://grok.com/chat/conversation-1",
        }[provider]
    return {
        "provider": provider,
        "items": [{
            "source_id": source_id,
            "title": "A real project discussion",
            "url": url,
            "source_date": "unknown-date",
        }],
    }


def _capture(provider="chatgpt", source_id="conversation-1", url=None, content="Keep the source intact"):
    if url is None:
        url = {
            "chatgpt": "https://chatgpt.com/c/conversation-1",
            "gemini": "https://gemini.google.com/app/conversation-1",
            "grok": "https://grok.com/chat/conversation-1",
        }[provider]
    return {
        "provider": provider,
        "source_id": source_id,
        "title": "A real project discussion",
        "url": url,
        "messages": [
            {"message_id": "m1", "role": "user", "content": content, "sequence": 0},
            {"message_id": "m2", "role": "assistant", "content": "Acknowledged.", "sequence": 1},
        ],
        "truncated": False,
        "history_start_reached": True,
        "adapter_version": "test",
    }


def test_browser_capture_routes_are_operator_only():
    for path, method in (
        ("/recovery/browser-capture/status", "GET"),
        ("/recovery/browser-capture/discover", "POST"),
        ("/recovery/browser-capture/next", "POST"),
        ("/recovery/browser-capture/capture", "POST"),
        ("/recovery/browser-capture/retry", "POST"),
    ):
        route = classify_request_path(path, method)
        assert route is not None
        assert route.scope is SecurityScope.OPERATOR


def test_discover_claim_archive_and_verify_local_capture(monkeypatch, tmp_path):
    client, ledger = _client(monkeypatch, tmp_path)
    discovered = client.post("/recovery/browser-capture/discover", json=_discovery())
    assert discovered.status_code == 200
    assert discovered.json()["registered"] == 1

    claimed = client.post("/recovery/browser-capture/next", json={})
    assert claimed.status_code == 200
    assert claimed.json()["next"]["source_id"] == "conversation-1"

    archived = client.post("/recovery/browser-capture/capture", json=_capture())
    assert archived.status_code == 200
    result = archived.json()
    assert result["status"] == "archived_and_hash_verified"
    assert result["message_count"] == 2
    assert result["full_history_verified"] is False

    path = Path(result["archive_path"])
    assert path.is_file()
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == result["sha256"]
    saved = ledger.get("chatgpt", "conversation-1")
    assert saved is not None
    assert saved.capture_status == "verified"
    assert saved.completeness == "visible_snapshot"
    assert saved.deletion_status == "not_eligible"
    record = json.loads(raw)
    assert [message["role"] for message in record["messages"]] == ["user", "assistant"]


def test_capture_is_idempotent_and_preserves_immutable_versions(monkeypatch, tmp_path):
    client, ledger = _client(monkeypatch, tmp_path)
    client.post("/recovery/browser-capture/discover", json=_discovery())
    client.post("/recovery/browser-capture/next", json={})

    first = client.post("/recovery/browser-capture/capture", json=_capture())
    second = client.post("/recovery/browser-capture/capture", json=_capture())
    changed = client.post(
        "/recovery/browser-capture/capture",
        json=_capture(content="Updated but still source-preserving"),
    )

    assert first.status_code == second.status_code == changed.status_code == 200
    assert second.json()["status"] == "already_archived"
    assert first.json()["sha256"] != changed.json()["sha256"]
    assert Path(first.json()["archive_path"]).is_file()
    assert Path(changed.json()["archive_path"]).is_file()
    assert first.json()["archive_path"] != changed.json()["archive_path"]
    assert ledger.get("chatgpt", "conversation-1").raw_sha256 == changed.json()["sha256"]


def test_rejects_unknown_provider_hosts_and_duplicate_message_sequences(monkeypatch, tmp_path):
    client, _ = _client(monkeypatch, tmp_path)
    bad = _discovery(url="https://example.com/c/conversation-1")
    assert client.post("/recovery/browser-capture/discover", json=bad).json()["registered"] == 0

    client.post("/recovery/browser-capture/discover", json=_discovery())
    client.post("/recovery/browser-capture/next", json={})
    payload = _capture()
    payload["messages"][1]["sequence"] = 0
    response = client.post("/recovery/browser-capture/capture", json=payload)
    assert response.status_code == 422


def test_grok_x_com_is_limited_to_grok_route(monkeypatch, tmp_path):
    client, _ = _client(monkeypatch, tmp_path)
    allowed = _discovery("grok", "grok-1", "https://x.com/i/grok?conversation=grok-1")
    blocked = _discovery("grok", "grok-2", "https://x.com/home")
    assert client.post("/recovery/browser-capture/discover", json=allowed).json()["registered"] == 1
    assert client.post("/recovery/browser-capture/discover", json=blocked).json()["registered"] == 0


def test_capture_requires_discovery_and_does_not_claim_full_history(monkeypatch, tmp_path):
    client, _ = _client(monkeypatch, tmp_path)
    response = client.post("/recovery/browser-capture/capture", json=_capture())
    assert response.status_code == 404
