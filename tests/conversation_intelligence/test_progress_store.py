from __future__ import annotations

import pytest

from core.conversation_intelligence.progress_store import ConversationProgressStore


def test_completed_conversation_is_not_reprocessed_on_next_cycle(tmp_path):
    store = ConversationProgressStore(tmp_path / "progress.sqlite3")
    fingerprint = store.fingerprint("export row v1")

    assert store.should_process("chatgpt", "conversation-1", fingerprint)
    store.record_conversation("chatgpt", "conversation-1", fingerprint, "Old conversation", result={"messages": 4})
    assert not store.should_process("chatgpt", "conversation-1", fingerprint)
    assert store.pending_conversations() == []


def test_changed_source_or_incomplete_work_is_eligible_for_processing(tmp_path):
    store = ConversationProgressStore(tmp_path / "progress.sqlite3")
    first = store.fingerprint("v1")
    second = store.fingerprint("v2")
    store.record_conversation("claude", "conversation-2", first, "Conversation", status="complete")
    assert store.should_process("claude", "conversation-2", second)

    store.record_conversation("claude", "conversation-3", first, "Interrupted", status="processing")
    assert store.should_process("claude", "conversation-3", first)
    assert [row["conversation_id"] for row in store.pending_conversations("claude")] == ["conversation-3"]


def test_source_cannot_be_marked_complete_when_import_is_partial(tmp_path):
    store = ConversationProgressStore(tmp_path / "progress.sqlite3")
    with pytest.raises(ValueError, match="all discovered"):
        store.record_source("chatgpt", "history-export", "fp", "complete", 10, 8)


def test_source_checkpoint_and_blocked_status_survive_reopen(tmp_path):
    db = tmp_path / "progress.sqlite3"
    store = ConversationProgressStore(db)
    store.record_source(
        "gemini", "account-history", "fp1", "blocked_login",
        discovered_count=12, imported_count=4, checkpoint="page:4", last_error="manual login required",
    )

    reopened = ConversationProgressStore(db)
    source = reopened.get_source("gemini", "account-history")
    assert source is not None
    assert source["status"] == "blocked_login"
    assert source["checkpoint"] == "page:4"
    assert source["imported_count"] == 4
    assert source["last_error"] == "manual login required"


def test_source_count_invariants_are_enforced(tmp_path):
    store = ConversationProgressStore(tmp_path / "progress.sqlite3")
    with pytest.raises(ValueError, match="0 <= imported_count"):
        store.record_source("chatgpt", "x", "fp", "partial", 2, 3)
