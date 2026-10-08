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