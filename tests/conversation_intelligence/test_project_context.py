from __future__ import annotations

import hashlib
import json

from core.conversation_intelligence.progress_store import ConversationProgressStore
from core.conversation_intelligence.project_context import (
    ProjectContextDossierGenerator,
    render_project_context,
)


def _snapshot(provider="chatgpt", cid="conv-1"):
    return {
        "conversation": {
            "conversation_id": cid,
            "provider": provider,
            "title": "DGM-MAT decisions",
            "content": "raw transcript remains elsewhere",
            "url": "https://example.invalid/conversation",
            "messages": [
                {"message_id": "u1", "role": "user", "content": "Keep original archives immutable.", "sequence": 0},
                {"message_id": "a1", "role": "assistant", "content": "I propose rewriting all archives.", "sequence": 1},
            ],
        },
        "artifacts": [{
            "artifact_id": "artifact-1",
            "language": "python",
            "code": "print('candidate')",
            "file_path": "candidate.py",
            "fingerprint": hashlib.sha256(b"print('candidate')").hexdigest(),
        }],
        "findings": [],
    }


def _store(tmp_path):
    store = ConversationProgressStore(tmp_path / "progress.sqlite")
    snapshot = _snapshot()
    store.record_conversation(
        "chatgpt", "conv-1", "source-fingerprint", "DGM-MAT decisions",
        status="complete", result=snapshot,
    )
    return store


def test_unmapped_conversations_are_not_guessed_or_written(tmp_path):
    result = ProjectContextDossierGenerator(_store(tmp_path), tmp_path / "out").build({})
    assert result["projects_written"] == 0
    assert result["conversations_unmapped"] == 1
    assert not (tmp_path / "out").exists()


def test_assistant_proposal_is_never_rendered_as_approved_decision():
    rendered = render_project_context("DGM-MAT", [{
        "provider": "chatgpt", "conversation_id": "conv-1", "title": "DGM",
        "messages": _snapshot()["conversation"]["messages"], "artifacts": [],
    }])
    assert "Keep original archives immutable." in rendered
    assert "I propose rewriting all archives." in rendered
    assert "AI proposals and assistant output (not approvals)" in rendered
    assert "No decision is promoted automatically." in rendered


def test_explicit_mapping_writes_provenance_manifest_and_code_hash(tmp_path):
    store = _store(tmp_path)
    source_db_hash_before = hashlib.sha256((tmp_path / "progress.sqlite").read_bytes()).hexdigest()
    generator = ProjectContextDossierGenerator(store, tmp_path / "out")
    result = generator.build({"chatgpt:conv-1": "DGM-MAT"})
    current = tmp_path / "out" / "DGM-MAT" / "PROJECT_CONTEXT.md"
    manifest_path = tmp_path / "out" / "DGM-MAT" / "manifest.json"
    assert result["projects_written"] == 1
    assert result["conversations_assigned"] == 1
    assert current.is_file()
    assert manifest_path.is_file()
    rendered = current.read_text(encoding="utf-8")
    assert "chatgpt:conv-1#message=u1" in rendered
    assert "Repository verification: not performed" in rendered
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["mapping_mode"] == "explicit_only"
    assert manifest["source_ids"] == ["chatgpt:conv-1"]
    assert manifest["sha256"] == hashlib.sha256(rendered.encode()).hexdigest()
    source_db_hash_after = hashlib.sha256((tmp_path / "progress.sqlite").read_bytes()).hexdigest()
    assert source_db_hash_after == source_db_hash_before


def test_render_is_deterministic_and_history_is_content_addressed(tmp_path):
    conversations = [{
        "provider": "chatgpt", "conversation_id": "conv-1", "title": "DGM",
        "messages": _snapshot()["conversation"]["messages"], "artifacts": _snapshot()["artifacts"],
    }]
    assert render_project_context("DGM-MAT", conversations) == render_project_context("DGM-MAT", conversations)
    generator = ProjectContextDossierGenerator(_store(tmp_path), tmp_path / "out")
    mapping = {"chatgpt:conv-1": "DGM-MAT"}
    first = generator.build(mapping)
    second = generator.build(mapping)
    assert first["outputs"][0]["sha256"] == second["outputs"][0]["sha256"]
    history = list((tmp_path / "out" / "DGM-MAT" / "history").glob("*.md"))
    assert len(history) == 1


def test_invalid_or_path_traversal_project_key_is_rejected(tmp_path):
    generator = ProjectContextDossierGenerator(_store(tmp_path), tmp_path / "out")
    try:
        generator.build({"chatgpt:conv-1": "../outside"})
    except ValueError:
        pass
    else:
        raise AssertionError("unsafe project key was accepted")
