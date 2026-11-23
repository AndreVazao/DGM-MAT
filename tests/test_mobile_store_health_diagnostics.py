from __future__ import annotations

import json

from core.mobile_runtime.store import ConversationStore


def test_missing_store_reports_non_recovery_state(tmp_path):
    store = ConversationStore(tmp_path / "missing.json")
    diagnostic = store.health_diagnostic()
    assert diagnostic["status"] == "missing"
    assert diagnostic["recovery_required"] is False
    assert diagnostic["loaded_threads"] == 0


def test_valid_empty_store_reports_healthy(tmp_path):
    path = tmp_path / "store.json"
    path.write_text(json.dumps({"threads": []}), encoding="utf-8")
    store = ConversationStore(path)
    diagnostic = store.health_diagnostic()
    assert diagnostic["status"] == "healthy"
    assert diagnostic["recovery_required"] is False


def test_malformed_json_reports_load_failed_without_path_leak(tmp_path):
    path = tmp_path / "private-conversation-store.json"
    path.write_text("{broken", encoding="utf-8")
    store = ConversationStore(path)
    diagnostic = store.health_diagnostic()
    assert diagnostic["status"] == "load_failed"
    assert diagnostic["recovery_required"] is True
    assert str(path) not in diagnostic["message"]


def test_invalid_thread_record_reports_recovery_required(tmp_path):
    path = tmp_path / "store.json"
    path.write_text(json.dumps({"threads": [{"id": "bad", "messages": "not-a-list"}]}), encoding="utf-8")
    store = ConversationStore(path)
    diagnostic = store.health_diagnostic()
    assert diagnostic["status"] == "recovery_required"
    assert diagnostic["recovery_required"] is True
    assert diagnostic["loaded_threads"] == 0
