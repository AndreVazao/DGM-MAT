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
    assert len(second) == 1  # cached audit remains available to downstream delegations
    assert calls == ["history-1"]
    assert pipeline.summarize(second)["conversation_count"] == 1
    assert pipeline.summarize()["conversation_count"] == 1
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



def test_cached_audit_snapshot_preserves_artifacts_for_consolidation(tmp_path):
    import json

    from core.conversation_intelligence.models import CodeArtifact, ConversationAudit
    from core.conversation_intelligence.pipeline import ConversationIntelligencePipeline

    export_path = tmp_path / "chatgpt.json"
    progress_path = tmp_path / "progress.sqlite3"
    export_path.write_text(json.dumps({"conversations": [{
        "id": "history-code",
        "title": "Python module",
        "content": "Build a utility",
    }]}), encoding="utf-8")

    pipeline = ConversationIntelligencePipeline(progress_store_path=progress_path)
    calls = []

    def audit(conversation, artifacts):
        calls.append(conversation.conversation_id)
        artifact = CodeArtifact(
            artifact_id="artifact-1",
            conversation_id=conversation.conversation_id,
            provider=conversation.provider,
            language="python",
            code="def useful():\n    return 42\n",
            file_path="useful.py",
            fingerprint="stable-artifact-fingerprint",
        )
        return ConversationAudit(conversation=conversation, artifacts=[artifact], suggested_project="DGM-MAT")

    pipeline.auditor.audit = audit
    first = pipeline.ingest_file(export_path, "chatgpt")
    second = pipeline.ingest_file(export_path, "chatgpt")

    assert calls == ["history-code"]
    assert len(first[0].artifacts) == len(second[0].artifacts) == 1
    assert second[0].artifacts[0].code == "def useful():\n    return 42\n"
    assert pipeline.summarize()["artifact_count"] == 1
    assert pipeline.consolidate()["unique_count"] == 1


def test_saved_audits_can_be_loaded_without_source_export(tmp_path):
    import json

    from core.conversation_intelligence.models import ConversationAudit
    from core.conversation_intelligence.pipeline import ConversationIntelligencePipeline

    export_path = tmp_path / "gemini.json"
    progress_path = tmp_path / "progress.sqlite3"
    export_path.write_text(json.dumps({"conversations": [{
        "id": "history-saved", "title": "Stored context", "content": "DGM-MAT project"
    }]}), encoding="utf-8")
    pipeline = ConversationIntelligencePipeline(progress_store_path=progress_path)
    pipeline.auditor.audit = lambda conversation, artifacts: ConversationAudit(
        conversation=conversation, artifacts=artifacts, suggested_project="DGM-MAT"
    )
    pipeline.ingest_file(export_path, "gemini")

    export_path.unlink()
    restored = pipeline.load_saved_audits()
    assert len(restored) == 1
    assert restored[0].conversation.conversation_id == "history-saved"
    assert restored[0].conversation.content == ""
    assert pipeline.summarize()["projects"] == ["DGM-MAT"]



def test_legacy_counter_only_snapshot_is_rebuilt_once(tmp_path):
    import json

    from core.conversation_intelligence.models import ConversationAudit
    from core.conversation_intelligence.pipeline import ConversationIntelligencePipeline

    export_path = tmp_path / "legacy.json"
    progress_path = tmp_path / "progress.sqlite3"
    export_path.write_text(json.dumps({"conversations": [{
        "id": "legacy-history", "title": "Old ledger item", "content": "Rebuild this result"
    }]}), encoding="utf-8")
    pipeline = ConversationIntelligencePipeline(progress_store_path=progress_path)
    conversation = pipeline.ingestor.load_file(export_path, "chatgpt")[0]
    fingerprint = pipeline.progress_store.fingerprint(json.dumps({
        "title": conversation.title,
        "content": conversation.content,
        "url": conversation.url,
        "messages": [],
    }, ensure_ascii=False, sort_keys=True))
    pipeline.progress_store.record_conversation(
        conversation.provider, conversation.conversation_id, fingerprint,
        conversation.title, status="complete",
        result={"artifact_count": 0, "finding_count": 0, "artifact_fingerprints": []},
    )
    calls = []
    pipeline.auditor.audit = lambda conversation, artifacts: (
        calls.append(conversation.conversation_id) or ConversationAudit(conversation=conversation, artifacts=artifacts)
    )

    first = pipeline.ingest_file(export_path, "chatgpt")
    second = pipeline.ingest_file(export_path, "chatgpt")
    assert calls == ["legacy-history"]
    assert len(first) == len(second) == 1


def test_delegation_context_reuses_cached_archive_and_open_review_tasks(tmp_path):
    import json

    from core.conversation_intelligence.models import ConversationAudit
    from core.conversation_intelligence.pipeline import ConversationIntelligencePipeline

    export_path = tmp_path / "delegation-context.json"
    progress_path = tmp_path / "progress.sqlite3"
    knowledge_path = tmp_path / "knowledge.sqlite3"
    export_path.write_text(json.dumps({"conversations": [{
        "id": "delegation-history", "title": "Prior project context", "content": "DGM-MAT archive"
    }]}), encoding="utf-8")

    pipeline = ConversationIntelligencePipeline(progress_path, knowledge_path)
    pipeline.auditor.audit = lambda conversation, artifacts: ConversationAudit(
        conversation=conversation, artifacts=artifacts, suggested_project="DGM-MAT"
    )
    pipeline.ingest_file(export_path, "chatgpt")
    pipeline.knowledge_store.create_review_task(
        task_id="review-delegation-1",
        item_type="decision",
        item_id="decision-legacy",
        reason="Confirm whether newer instruction supersedes an old approach",
        evidence=["delegation-history#message-4"],
    )
    export_path.unlink()

    context = pipeline.build_delegation_context()
    assert context["archive_summary"]["conversation_count"] == 1
    assert context["conversations"][0]["conversation_id"] == "delegation-history"
    assert context["open_review_tasks"][0]["task_id"] == "review-delegation-1"
    assert context["knowledge"]["summary"]["review_tasks_open"] == 1



def test_unchanged_completed_source_reuses_cached_audits_without_parsing_export(tmp_path):
    import json
    import pytest

    from core.conversation_intelligence.models import ConversationAudit
    from core.conversation_intelligence.pipeline import ConversationIntelligencePipeline

    export_path = tmp_path / "stable-source.json"
    export_path.write_text(json.dumps({"conversations": [{
        "id": "stable-conversation", "title": "Cached source", "content": "Reuse this result"
    }]}), encoding="utf-8")
    pipeline = ConversationIntelligencePipeline(progress_store_path=tmp_path / "progress.sqlite3")
    audited = []
    pipeline.auditor.audit = lambda conversation, artifacts: (
        audited.append(conversation.conversation_id)
        or ConversationAudit(conversation=conversation, artifacts=artifacts, suggested_project="DGM-MAT")
    )

    first = pipeline.ingest_file(export_path, "chatgpt")
    assert len(first) == 1
    assert audited == ["stable-conversation"]

    def unexpected_parse(*args, **kwargs):
        pytest.fail("unchanged completed source should reuse its source-level snapshot index")

    pipeline.ingestor.load_file = unexpected_parse
    second = pipeline.ingest_file(export_path, "chatgpt")
    assert len(second) == 1
    assert second[0].conversation.conversation_id == "stable-conversation"
    assert second[0].suggested_project == "DGM-MAT"
    assert audited == ["stable-conversation"]



def test_missing_source_snapshot_index_falls_back_to_parser_and_repairs_ledger(tmp_path):
    import json

    from core.conversation_intelligence.models import ConversationAudit
    from core.conversation_intelligence.pipeline import ConversationIntelligencePipeline

    export_path = tmp_path / "recoverable-source.json"
    progress_path = tmp_path / "progress.sqlite3"
    export_path.write_text(json.dumps({"conversations": [{
        "id": "recoverable-conversation", "title": "Recovery", "content": "Restore missing cache"
    }]}), encoding="utf-8")
    pipeline = ConversationIntelligencePipeline(progress_store_path=progress_path)
    audit_calls = []
    pipeline.auditor.audit = lambda conversation, artifacts: (
        audit_calls.append(conversation.conversation_id)
        or ConversationAudit(conversation=conversation, artifacts=artifacts, suggested_project="DGM-MAT")
    )
    first = pipeline.ingest_file(export_path, "chatgpt")
    assert len(first) == 1

    source_key = str(export_path.resolve())
    fingerprint = pipeline.progress_store.fingerprint(export_path.read_bytes())
    pipeline.progress_store.set_source_conversations("chatgpt", source_key, fingerprint, [])

    parse_calls = []
    original_load_file = pipeline.ingestor.load_file
    def tracked_parse(*args, **kwargs):
        parse_calls.append(True)
        return original_load_file(*args, **kwargs)
    pipeline.ingestor.load_file = tracked_parse

    recovered = pipeline.ingest_file(export_path, "chatgpt")
    assert len(recovered) == 1
    assert recovered[0].suggested_project == "DGM-MAT"
    assert parse_calls == [True]
    assert audit_calls == ["recoverable-conversation"]
    assert pipeline.progress_store.list_source_conversations("chatgpt", source_key, fingerprint) == [
        "recoverable-conversation"
    ]
    assert pipeline.progress_store.get_source("chatgpt", source_key)["status"] == "complete"


def test_interrupted_source_import_resumes_without_reauditing_completed_conversations(tmp_path):
    import json

    from core.conversation_intelligence.models import ConversationAudit
    from core.conversation_intelligence.pipeline import ConversationIntelligencePipeline

    export_path = tmp_path / "interrupted.json"
    export_path.write_text(json.dumps({"conversations": [
        {"id": "first-item", "title": "First", "content": "Already processed"},
        {"id": "second-item", "title": "Second", "content": "Fails once"},
    ]}), encoding="utf-8")
    pipeline = ConversationIntelligencePipeline(progress_store_path=tmp_path / "progress.sqlite3")
    calls = []

    def fail_second_once(conversation, artifacts):
        calls.append(conversation.conversation_id)
        if conversation.conversation_id == "second-item" and calls.count("second-item") == 1:
            raise RuntimeError("simulated interruption")
        return ConversationAudit(conversation=conversation, artifacts=artifacts)

    pipeline.auditor.audit = fail_second_once
    with pytest.raises(RuntimeError, match="simulated interruption"):
        pipeline.ingest_file(export_path, "chatgpt")

    source_key = str(export_path.resolve())
    failed = pipeline.progress_store.get_source("chatgpt", source_key)
    assert failed["status"] == "failed"
    assert failed["imported_count"] == 1
    assert pipeline.progress_store.get_conversation("chatgpt", "first-item")["status"] == "complete"
    assert pipeline.progress_store.get_conversation("chatgpt", "second-item")["status"] == "failed"

    recovered = pipeline.ingest_file(export_path, "chatgpt")
    assert [audit.conversation.conversation_id for audit in recovered] == ["first-item", "second-item"]
    assert calls == ["first-item", "second-item", "second-item"]
    completed = pipeline.progress_store.get_source("chatgpt", source_key)
    assert completed["status"] == "complete"
    assert completed["imported_count"] == completed["discovered_count"] == 2
    assert pipeline.progress_store.list_source_conversations(
        "chatgpt", source_key, pipeline.progress_store.fingerprint(export_path.read_bytes())
    ) == ["first-item", "second-item"]


def test_changed_source_invalidates_source_cache_and_updates_conversation_snapshot(tmp_path):
    import json

    from core.conversation_intelligence.models import ConversationAudit
    from core.conversation_intelligence.pipeline import ConversationIntelligencePipeline

    export_path = tmp_path / "changed-source.json"
    progress_path = tmp_path / "progress.sqlite3"
    export_path.write_text(json.dumps({"conversations": [
        {"id": "mutable-item", "title": "Original title", "content": "Original content"},
    ]}), encoding="utf-8")
    pipeline = ConversationIntelligencePipeline(progress_store_path=progress_path)
    calls = []

    def audit(conversation, artifacts):
        calls.append((conversation.conversation_id, conversation.title, conversation.content))
        return ConversationAudit(conversation=conversation, artifacts=artifacts, suggested_title=conversation.title)

    pipeline.auditor.audit = audit
    first = pipeline.ingest_file(export_path, "chatgpt")
    assert first[0].suggested_title == "Original title"

    export_path.write_text(json.dumps({"conversations": [
        {"id": "mutable-item", "title": "Updated title", "content": "Updated content"},
    ]}), encoding="utf-8")
    second = pipeline.ingest_file(export_path, "chatgpt")

    assert len(second) == 1
    assert second[0].suggested_title == "Updated title"
    assert calls == [
        ("mutable-item", "Original title", "Original content"),
        ("mutable-item", "Updated title", "Updated content"),
    ]
    source = pipeline.progress_store.get_source("chatgpt", str(export_path.resolve()))
    assert source["status"] == "complete"
    assert source["source_fingerprint"] == pipeline.progress_store.fingerprint(export_path.read_bytes())


def test_source_cache_rejects_global_snapshot_from_another_export_with_same_conversation_id(tmp_path):
    import json

    from core.conversation_intelligence.models import ConversationAudit
    from core.conversation_intelligence.pipeline import ConversationIntelligencePipeline

    progress_path = tmp_path / "progress.sqlite3"
    first_path = tmp_path / "first-export.json"
    second_path = tmp_path / "second-export.json"
    first_path.write_text(json.dumps({"conversations": [{
        "id": "shared-id", "title": "First export", "content": "first content"
    }]}), encoding="utf-8")
    second_path.write_text(json.dumps({"conversations": [{
        "id": "shared-id", "title": "Second export", "content": "second content"
    }]}), encoding="utf-8")

    pipeline = ConversationIntelligencePipeline(progress_store_path=progress_path)
    audited = []

    def audit(conversation, artifacts):
        audited.append((conversation.title, conversation.content))
        return ConversationAudit(
            conversation=conversation, artifacts=artifacts, suggested_title=conversation.title
        )

    pipeline.auditor.audit = audit
    first_result = pipeline.ingest_file(first_path, "chatgpt")
    assert first_result[0].suggested_title == "First export"
    second_result = pipeline.ingest_file(second_path, "chatgpt")
    assert second_result[0].suggested_title == "Second export"

    parse_calls = []
    original_load_file = pipeline.ingestor.load_file

    def tracked_parse(*args, **kwargs):
        parse_calls.append(True)
        return original_load_file(*args, **kwargs)

    pipeline.ingestor.load_file = tracked_parse
    restored_first = pipeline.ingest_file(first_path, "chatgpt")

    assert parse_calls == [True], "cache must fall back when the global snapshot belongs to another source version"
    assert restored_first[0].suggested_title == "First export"
    assert audited == [
        ("First export", "first content"),
        ("Second export", "second content"),
        ("First export", "first content"),
    ]


def test_existing_source_membership_schema_is_migrated_without_losing_rows(tmp_path):
    import sqlite3

    from core.conversation_intelligence.progress_store import ConversationProgressStore

    database = tmp_path / "legacy-progress.sqlite3"
    with sqlite3.connect(database) as db:
        db.execute("""
            CREATE TABLE source_conversations (
                provider TEXT NOT NULL,
                source_key TEXT NOT NULL,
                source_fingerprint TEXT NOT NULL,
                conversation_id TEXT NOT NULL,
                ordinal INTEGER NOT NULL,
                PRIMARY KEY (provider, source_key, ordinal)
            )
        """)
        db.execute(
            "INSERT INTO source_conversations VALUES (?, ?, ?, ?, ?)",
            ("chatgpt", "old-export.json", "source-fp", "old-conversation", 0),
        )
    db.close()

    store = ConversationProgressStore(database)
    members = store.list_source_conversation_members("chatgpt", "old-export.json", "source-fp")
    assert members == [{
        "conversation_id": "old-conversation",
        "conversation_fingerprint": None,
    }]
    with sqlite3.connect(database) as db:
        columns = {row[1] for row in db.execute("PRAGMA table_info(source_conversations)")}
    assert "conversation_fingerprint" in columns


def test_source_membership_rejects_mismatched_fingerprint_count(tmp_path):
    store = ConversationProgressStore(tmp_path / "progress.sqlite3")
    with pytest.raises(ValueError, match="matching lengths"):
        store.set_source_conversations(
            "chatgpt", "source.json", "source-fp",
            ["conversation-1", "conversation-2"],
            ["conversation-fp-1"],
        )
