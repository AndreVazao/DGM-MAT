import json
from pathlib import Path
from core.conversation_intelligence import ConversationIntelligencePipeline

def test_extracts_python_and_detects_syntax_error(tmp_path: Path):
    source = tmp_path / "chatgpt.json"
    source.write_text('{"conversations":[{"id":"1","title":"DGM-MAT repair","content":"Use this file.\\n```python\\ndef broken(:\\n    pass\\n```"}]}', encoding="utf-8")
    audits = ConversationIntelligencePipeline().ingest_file(source, "chatgpt")
    assert len(audits) == 1
    assert len(audits[0].artifacts) == 1
    assert audits[0].artifacts[0].syntax_ok is False
    assert any(f.category == "syntax" for f in audits[0].findings)

def test_consolidates_duplicate_code(tmp_path: Path):
    source = tmp_path / "claude.json"
    source.write_text('{"conversations":[{"id":"1","title":"DGM-MAT","content":"```python\\nprint(1)\\n```"},{"id":"2","title":"DGM-MAT again","content":"```python\\nprint(1)\\n```"}]}', encoding="utf-8")
    pipeline = ConversationIntelligencePipeline()
    audits = pipeline.ingest_file(source, "claude")
    result = pipeline.consolidate(audits)
    assert result["artifact_count"] == 2
    assert result["unique_count"] == 1
    assert len(result["duplicate_groups"]) == 1


def test_progress_store_preserves_full_user_and_assistant_messages(tmp_path: Path):
    source = tmp_path / "chatgpt.json"
    source.write_text(
        json.dumps({
            "conversations": [{
                "id": "conversation-with-messages",
                "title": "DGM-MAT history",
                "url": "https://chatgpt.com/c/conversation-with-messages",
                "messages": [
                    {"id": "user-1", "role": "user", "content": "Keep the original project context."},
                    {"id": "assistant-1", "role": "assistant", "content": "I will preserve the source and decisions."},
                ],
            }]
        }),
        encoding="utf-8",
    )
    pipeline = ConversationIntelligencePipeline(progress_store_path=tmp_path / "progress.sqlite3")

    first = pipeline.ingest_file(source, "chatgpt")
    restored = pipeline.load_saved_audits()
    cached = pipeline.ingest_file(source, "chatgpt")
    compact_context = pipeline.build_delegation_context()
    full_context = pipeline.build_delegation_context(include_messages=True)

    assert [message.role for message in first[0].conversation.messages] == ["user", "assistant"]
    assert [message.content for message in restored[0].conversation.messages] == [
        "Keep the original project context.",
        "I will preserve the source and decisions.",
    ]
    assert [message.message_id for message in cached[0].conversation.messages] == ["user-1", "assistant-1"]
    assert compact_context["conversations"][0]["message_count"] == 2
    assert compact_context["conversations"][0]["messages"] == []
    assert [message["role"] for message in full_context["conversations"][0]["messages"]] == [
        "user", "assistant"
    ]
