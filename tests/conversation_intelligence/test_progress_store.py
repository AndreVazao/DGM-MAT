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

def test_pipeline_persists_results_and_skips_unchanged_history(tmp_path):
    import json

    from core.conversation_intelligence.models import ConversationAudit
    from core.conversation_intelligence.pipeline import ConversationIntelligencePipeline

    export_path = tmp_path / "chatgpt.json"
    progress_path = tmp_path / "progress.sqlite3"
    export_path.write_text(json.dumps({
        "conversations": [{
            "id": "history-1",
            "title": "Old finished conversation",
            "messages": [{"id": "m1", "role": "user", "content": "Already documented"}],
        }]
    }), encoding="utf-8")

    pipeline = ConversationIntelligencePipeline(progress_store_path=progress_path)
    calls = []
    pipeline.auditor.audit = lambda conversation, artifacts: (
        calls.append(conversation.conversation_id) or ConversationAudit(conversation=conversation, artifacts=artifacts)
    )

    first = pipeline.ingest_file(export_path, "chatgpt")
    second = pipeline.ingest_file(export_path, "chatgpt")

    assert len(first) == 1
    assert second == []
    assert calls == ["history-1"]
    store = ConversationProgressStore(progress_path)
    assert store.get_source("chatgpt", str(export_path.resolve()))["status"] == "complete"
    assert store.summary()["conversations_complete"] == 1


def test_pipeline_reprocesses_only_when_conversation_content_changes(tmp_path):
    import json

    from core.conversation_intelligence.models import ConversationAudit
    from core.conversation_intelligence.pipeline import ConversationIntelligencePipeline

    export_path = tmp_path / "claude.json"
    export_path.write_text(json.dumps({"conversations": [{
        "id": "history-2", "title": "Conversation", "content": "version one"
    }]}), encoding="utf-8")
    pipeline = ConversationIntelligencePipeline(progress_store_path=tmp_path / "progress.sqlite3")
    calls = []
    pipeline.auditor.audit = lambda conversation, artifacts: (
        calls.append(conversation.content) or ConversationAudit(conversation=conversation, artifacts=artifacts)
    )

    pipeline.ingest_file(export_path, "claude")
    export_path.write_text(json.dumps({"conversations": [{
        "id": "history-2", "title": "Conversation", "content": "version two"
    }]}), encoding="utf-8")
    pipeline.ingest_file(export_path, "claude")

    assert calls == ["version one", "version two"]
