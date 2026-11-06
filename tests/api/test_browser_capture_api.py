from __future__ import annotations

import hashlib
import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.api import browser_capture_api
from core.api.security_policy import SecurityScope, classify_request_path
from core.recovery.recovery_ledger import RecoveryLedger
from core.vault import VaultCatalog


def _client(monkeypatch, tmp_path):
    ledger = RecoveryLedger(tmp_path / "ledger.sqlite3")
    monkeypatch.setattr(browser_capture_api, "_ledger", lambda: ledger)
    monkeypatch.setenv("DGM_RECOVERY_ARCHIVE_ROOT", str(tmp_path / "archive"))
    from core.conversation_intelligence import pipeline as pipeline_module
    from core.storage.storage_manager import storage_manager

    class FakePipeline:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            from core.conversation_intelligence.knowledge_store import ConversationKnowledgeStore
            self.knowledge_store = ConversationKnowledgeStore(kwargs["knowledge_store_path"])

        def ingest_file(self, path, provider=None):
            self.path = Path(path)
            self.provider = provider
            return []

        def summarize(self, audits):
            return {"conversation_count": 1, "artifact_count": 0, "projects": [], "errors": 0, "warnings": 0}

    monkeypatch.setattr(pipeline_module, "ConversationIntelligencePipeline", FakePipeline)
    monkeypatch.setattr(storage_manager, "get_path", lambda name: tmp_path / "storage" / name)
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
        "history_start_reached": False,
        "adapter_version": "test",
    }


def test_browser_capture_routes_use_narrow_extension_scope():
    for path, method in (
        ("/recovery/browser-capture/status", "GET"),
        ("/recovery/browser-capture/discover", "POST"),
        ("/recovery/browser-capture/next", "POST"),
        ("/recovery/browser-capture/capture", "POST"),
        ("/recovery/browser-capture/block", "POST"),
        ("/recovery/browser-capture/retry", "POST"),
    ):
        route = classify_request_path(path, method)
        assert route is not None
        assert route.scope is SecurityScope.BROWSER_CAPTURE


def test_discover_claim_archive_and_verify_local_capture(monkeypatch, tmp_path):
    client, ledger = _client(monkeypatch, tmp_path)
    discovered = client.post("/recovery/browser-capture/discover", json=_discovery())
    assert discovered.status_code == 200
    assert discovered.json()["registered"] == 1
    assert discovered.json()["pending"] == 1

    claimed = client.post("/recovery/browser-capture/next", json={"provider": "chatgpt"})
    assert claimed.status_code == 200
    assert claimed.json()["next"]["source_id"] == "conversation-1"

    archived = client.post("/recovery/browser-capture/capture", json=_capture())
    assert archived.status_code == 200
    result = archived.json()
    assert result["status"] == "archived_and_hash_verified"
    assert result["message_count"] == 2
    assert result["full_history_verified"] is False
    assert result["history_completeness"] == "partial_or_unknown"
    assert result["oldest_boundary"] == "unknown"

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
    client.post("/recovery/browser-capture/next", json={"provider": "chatgpt"})

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
    client.post("/recovery/browser-capture/next", json={"provider": "chatgpt"})
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


def test_provider_block_is_checkpointed_without_retry_or_bypass(monkeypatch, tmp_path):
    client, ledger = _client(monkeypatch, tmp_path)
    client.post("/recovery/browser-capture/discover", json=_discovery())
    client.post("/recovery/browser-capture/next", json={"provider": "chatgpt"})
    response = client.post("/recovery/browser-capture/block", json={
        "provider": "chatgpt",
        "source_id": "conversation-1",
        "status": "blocked",
        "reason": "blocked_login",
    })
    assert response.status_code == 200
    assert ledger.get("chatgpt", "conversation-1").capture_status == "blocked"
    assert client.post("/recovery/browser-capture/next", json={"provider": "chatgpt"}).json()["status"] == "queue_empty"


def test_raw_capture_is_preserved_and_redacted_copy_is_indexed(monkeypatch, tmp_path):
    client, _ = _client(monkeypatch, tmp_path)
    client.post("/recovery/browser-capture/discover", json=_discovery())
    client.post("/recovery/browser-capture/next", json={"provider": "chatgpt"})
    payload = _capture(content="Example configuration: api_key=sk-abcdefghijklmnopqrstuvwxyz123456")
    response = client.post("/recovery/browser-capture/capture", json=payload)
    assert response.status_code == 200
    result = response.json()
    assert result["index_status"] == "indexed"
    raw = Path(result["archive_path"]).read_text(encoding="utf-8")
    normalized = Path(result["normalized_archive_path"]).read_text(encoding="utf-8")
    assert "sk-abcdefghijklmnopqrstuvwxyz123456" in raw
    assert "sk-abcdefghijklmnopqrstuvwxyz123456" not in normalized
    assert "[REDACTED" in normalized
    normalized_record = json.loads(normalized)
    assert normalized_record["messages"][0]["role"] == "user"
    assert result["index_summary"]["conversation_count"] == 1
    assert result["index_summary"]["intent_candidates"] == 1
    assert result["index_summary"]["proposal_candidates"] == 0
    assert result["index_summary"]["confirmed_decisions_created"] == 0
    assert result["index_summary"]["knowledge"]["intents"] == 1
    assert result["index_summary"]["knowledge"]["decisions"] == 0


def test_ai_proposals_are_candidates_and_operator_confirmation_is_not_auto_decision(monkeypatch, tmp_path):
    client, _ = _client(monkeypatch, tmp_path)
    client.post("/recovery/browser-capture/discover", json=_discovery())
    client.post("/recovery/browser-capture/next", json={"provider": "chatgpt"})
    payload = _capture()
    payload["top_load_steps"] = 7
    payload["top_load_limit_reached"] = True
    payload["truncated"] = True
    payload["messages"] = [
        {"message_id": "u1", "role": "user", "content": "Aprovo esta proposta, mas confirma primeiro o projeto.", "sequence": 0},
        {"message_id": "a1", "role": "assistant", "content": "I recommend keeping the current DGM-MAT recovery architecture.", "sequence": 1},
    ]
    response = client.post("/recovery/browser-capture/capture", json=payload)
    assert response.status_code == 200
    summary = response.json()["index_summary"]
    assert summary["intent_candidates"] == 1
    assert summary["proposal_candidates"] == 1
    assert summary["confirmed_decisions_created"] == 0
    assert summary["knowledge"]["decisions"] == 0
    assert summary["knowledge"]["proposals"] == 1
    assert summary["knowledge"]["review_tasks_open"] >= 2
    saved = json.loads(Path(response.json()["archive_path"]).read_text(encoding="utf-8"))
    assert saved["top_load_steps"] == 7
    assert saved["top_load_limit_reached"] is True
    assert saved["truncated"] is True


def test_discovery_rejects_source_id_that_does_not_match_conversation_url(monkeypatch, tmp_path):
    client, ledger = _client(monkeypatch, tmp_path)
    payload = _discovery(source_id="wrong-id", url="https://chatgpt.com/c/real-id")
    response = client.post("/recovery/browser-capture/discover", json=payload)
    assert response.status_code == 200
    assert response.json()["registered"] == 0
    assert ledger.source_count() == 0


def test_rediscovery_does_not_requeue_already_verified_conversation(monkeypatch, tmp_path):
    client, _ = _client(monkeypatch, tmp_path)
    client.post("/recovery/browser-capture/discover", json=_discovery())
    client.post("/recovery/browser-capture/next", json={"provider": "chatgpt"})
    client.post("/recovery/browser-capture/capture", json=_capture())
    response = client.post("/recovery/browser-capture/discover", json=_discovery())
    assert response.status_code == 200
    assert response.json()["registered"] == 1
    assert response.json()["pending"] == 0
    assert response.json()["already_processed"] == 1


def test_provider_scoped_next_never_claims_another_ai_queue(monkeypatch, tmp_path):
    client, _ = _client(monkeypatch, tmp_path)
    chat = _discovery("chatgpt", "conversation-1")
    gemini = _discovery("gemini", "conversation-2", "https://gemini.google.com/app/conversation-2")
    client.post("/recovery/browser-capture/discover", json=chat)
    client.post("/recovery/browser-capture/discover", json=gemini)

    chat_next = client.post("/recovery/browser-capture/next", json={"provider": "chatgpt"}).json()
    gemini_next = client.post("/recovery/browser-capture/next", json={"provider": "gemini"}).json()
    assert chat_next["next"]["provider"] == "chatgpt"
    assert gemini_next["next"]["provider"] == "gemini"


def test_discovery_reports_when_visible_list_scan_hits_bound(monkeypatch, tmp_path):
    client, _ = _client(monkeypatch, tmp_path)
    payload = _discovery()
    payload["truncated"] = True
    response = client.post("/recovery/browser-capture/discover", json=payload)
    assert response.status_code == 200
    assert response.json()["discovery_truncated"] is True


def test_retry_unknown_source_returns_not_found(monkeypatch, tmp_path):
    client, _ = _client(monkeypatch, tmp_path)
    response = client.post(
        "/recovery/browser-capture/retry?provider=chatgpt&source_id=missing",
        json={},
    )
    assert response.status_code == 404


def test_browser_capture_reuses_the_shared_recovery_ledger(monkeypatch, tmp_path):
    shared = RecoveryLedger(tmp_path / "shared.sqlite3")
    monkeypatch.setattr(browser_capture_api, "get_recovery_ledger", lambda: shared)
    assert browser_capture_api._ledger() is shared


def test_immutable_archive_writer_is_atomic_and_never_overwrites(tmp_path):
    destination = tmp_path / "immutable.json"
    assert browser_capture_api._write_immutable_bytes(destination, b"first-version") is True
    assert browser_capture_api._write_immutable_bytes(destination, b"second-version") is False
    assert destination.read_bytes() == b"first-version"
    assert list(tmp_path.glob(".dgm-capture-*.tmp")) == []


def test_browser_capture_writes_raw_and_normalized_conversation_to_persistent_vault(monkeypatch, tmp_path):
    client, _ = _client(monkeypatch, tmp_path)
    vault_root = tmp_path / "persistent-vault"
    monkeypatch.setenv("DGM_VAULT_PATH", str(vault_root))
    client.post("/recovery/browser-capture/discover", json=_discovery())
    client.post("/recovery/browser-capture/next", json={"provider": "chatgpt"})

    response = client.post("/recovery/browser-capture/capture", json=_capture(content="DGM-MAT persistent memory"))
    assert response.status_code == 200
    result = response.json()
    raw_path = Path(result["archive_path"])
    assert raw_path.is_relative_to(vault_root / "providers" / "browser-ui")
    assert raw_path.is_file()
    assert Path(result["normalized_archive_path"]).is_file()
    assert result["index_summary"]["vault_archive"]["status"] == "archived"
    vault = VaultCatalog(vault_root)
    records = vault.list_conversations("dgm-mat")
    assert len(records) == 1
    assert records[0]["provider"] == "chatgpt"
    assert records[0]["completeness"] == "partial_or_unknown"
    assert Path(records[0]["archive_path"]).is_file()
