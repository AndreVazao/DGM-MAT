from __future__ import annotations

import json

import pytest

from core.conversation_intelligence.ingest import ConversationIngestor
from core.conversation_intelligence.models import ImportCoverage, UserDecision, UserIntent


def test_json_ingest_preserves_user_and_assistant_as_distinct_ordered_messages():
    payload = {
        "conversations": [{
            "id": "conv-1",
            "title": "DGM-MAT memory recovery",
            "messages": [
                {"id": "m1", "role": "user", "content": "Recover conversation history first.", "timestamp": "2026-10-01T10:00:00Z"},
                {"id": "m2", "role": "assistant", "content": "I propose a browser importer.", "timestamp": "2026-10-01T10:00:05Z"},
                {"id": "m3", "role": "user", "content": "Approved, but do not bypass MFA.", "timestamp": "2026-10-01T10:01:00Z"},
            ],
        }]
    }
    record = ConversationIngestor().from_json(json.dumps(payload), "chatgpt")[0]

    assert [message.role for message in record.messages] == ["user", "assistant", "user"]
    assert [message.sequence for message in record.messages] == [0, 1, 2]
    assert record.messages[0].content == "Recover conversation history first."
    assert record.messages[1].content == "I propose a browser importer."
    assert record.messages[2].timestamp == "2026-10-01T10:01:00Z"


def test_unknown_speaker_is_not_invented_when_export_has_no_role():
    payload = {"conversations": [{"id": "conv-2", "messages": [{"content": "Ambiguous source message"}]}]}
    record = ConversationIngestor().from_json(json.dumps(payload))[0]
    assert len(record.messages) == 1
    assert record.messages[0].role == "unknown"


def test_openai_mapping_export_keeps_explicit_author_and_timestamp_order():
    payload = {
        "conversations": [{
            "id": "conv-3",
            "mapping": {
                "b": {"message": {"id": "b", "author": {"role": "assistant"}, "content": {"parts": ["Answer"]}, "create_time": 2}},
                "a": {"message": {"id": "a", "author": {"role": "user"}, "content": {"parts": ["Question"]}, "create_time": 1}},
            },
        }]
    }
    record = ConversationIngestor().from_json(json.dumps(payload), "chatgpt")[0]
    assert [(m.role, m.content, m.timestamp) for m in record.messages] == [
        ("user", "Question", "1"),
        ("assistant", "Answer", "2"),
    ]


def test_intent_and_decision_defaults_are_unverified_not_confirmed():
    intent = UserIntent(intent_id="i1", statement="Recover history")
    decision = UserDecision(decision_id="d1", statement="Use browser session")
    assert intent.status == "unverified"
    assert not intent.reviewed_by_user
    assert decision.status == "unverified"
    assert not decision.confirmed_by_user


def test_import_coverage_refuses_false_complete_claim():
    coverage = ImportCoverage(provider="chatgpt", status="complete", discovered_count=10, imported_count=8)
    with pytest.raises(ValueError, match="Complete coverage"):
        coverage.validate()


def test_import_coverage_rejects_invalid_counts():
    with pytest.raises(ValueError, match="cannot be negative"):
        ImportCoverage(provider="chatgpt", discovered_count=-1).validate()
    with pytest.raises(ValueError, match="cannot exceed"):
        ImportCoverage(provider="chatgpt", discovered_count=2, imported_count=3).validate()
    with pytest.raises(ValueError, match="cannot exceed"):
        ImportCoverage(provider="chatgpt", discovered_count=0, imported_count=1).validate()
