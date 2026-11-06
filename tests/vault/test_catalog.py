import json
import sqlite3
from pathlib import Path

import pytest

from core.vault import VaultCatalog


def test_vault_requires_explicit_persistent_root(monkeypatch):
    monkeypatch.delenv("DGM_VAULT_PATH", raising=False)
    with pytest.raises(ValueError, match="Vault path is required"):
        VaultCatalog()


def test_archive_is_immutable_and_byte_identical_imports_are_linked_as_duplicates(tmp_path):
    vault = VaultCatalog(tmp_path / "AndreOS-Vault")
    vault.register_project("dgm-mat", "DGM-MAT", aliases=["DGM MAT"])
    payload = dict(provider="chatgpt", conversation_id="conv-1", title="DGM-MAT fixing",
                   messages=[{"id": "u1", "role": "user", "content": "Fix DGM-MAT"}],
                   completeness="partial_dom_snapshot", project_id="dgm-mat")
    first = vault.archive_conversation(**payload)
    second = vault.archive_conversation(**payload)
    archived = Path(first["archive_path"])
    original = archived.read_bytes()

    assert first["status"] == "archived"
    assert second["status"] == "duplicate"
    assert archived.read_bytes() == original
    assert vault.summary()["duplicate_candidates"] == 1
    assert vault.summary()["conversations"] == 1


def test_unclassified_conversation_is_quarantined_not_guessed(tmp_path):
    vault = VaultCatalog(tmp_path / "vault")
    vault.register_project("dgm-mat", "DGM-MAT", aliases=["DGM-MAT"])
    result = vault.archive_conversation(provider="grok", conversation_id="x", title="Cooking",
                                        messages=[], content="Recipe", completeness="unknown")
    assert result["project_id"] is None
    assert result["assignment_status"] == "unclassified"
    assert Path(result["archive_path"]).is_relative_to(tmp_path / "vault" / "quarantine")


def test_project_suggestion_keeps_provenance_and_does_not_mark_user_reviewed(tmp_path):
    vault = VaultCatalog(tmp_path / "vault")
    vault.register_project("dgm-mat", "DGM-MAT", aliases=["DGM-MAT", "AndreOS"])
    result = vault.archive_conversation(provider="gemini", conversation_id="g1", title="DGM-MAT browser recovery",
                                        messages=[{"role": "user", "content": "AndreOS"}],
                                        completeness="partial")
    assert result["project_id"] == "dgm-mat"
    assert result["assignment_status"] == "suggested"
    row = vault.list_conversations("dgm-mat")[0]
    assert row["assignment_status"] == "suggested"
    assert row["assignment_evidence"]


def test_repository_snapshot_ignores_generated_and_symlinked_directories(tmp_path):
    root = tmp_path / "repo"
    (root / "src").mkdir(parents=True)
    (root / "src" / "main.py").write_text("print('ok')", encoding="utf-8")
    (root / "package.json").write_text("{}", encoding="utf-8")
    (root / "node_modules").mkdir()
    (root / "node_modules" / "large.js").write_text("ignored", encoding="utf-8")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("not followed", encoding="utf-8")
    try:
        (root / "linked").symlink_to(outside, target_is_directory=True)
    except OSError:
        pass

    vault = VaultCatalog(tmp_path / "vault")
    vault.register_project("sample", "Sample", root)
    snapshot = vault.snapshot_repository("sample", root)
    data = json.loads(Path(snapshot["snapshot_path"]).read_text(encoding="utf-8"))

    assert "src/main.py" in {item["path"] for item in data["entries"]}
    assert "package.json" in data["manifests"]
    assert not any("node_modules" in item["path"] for item in data["entries"])
    assert not any(item["path"].startswith("linked/") for item in data["entries"])
    assert snapshot["languages"]["Python"] == 1
    tree_text = Path(snapshot["tree_text_path"]).read_text(encoding="utf-8")
    assert "src/" in tree_text and "main.py" in tree_text
    current = json.loads(Path(snapshot["current_pointer"]).read_text(encoding="utf-8"))
    assert current["snapshot_id"] == snapshot["snapshot_id"]


def test_tree_limit_fails_without_writing_partial_snapshot(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    for index in range(5):
        (root / f"file-{index}.txt").write_text("x", encoding="utf-8")
    vault = VaultCatalog(tmp_path / "vault")
    vault.register_project("sample", "Sample", root)
    with pytest.raises(ValueError, match="max_entries"):
        vault.snapshot_repository("sample", root, max_entries=3)
    assert not list((tmp_path / "vault" / "projects" / "sample" / "trees").glob("*.json"))


def test_reinstall_independent_catalog_reopens_from_same_vault(tmp_path):
    path = tmp_path / "portable-vault"
    first = VaultCatalog(path)
    first.register_project("office-kit", "Office Kit")
    first.archive_conversation(provider="chatgpt", conversation_id="office-1", title="Office Kit",
                               messages=[{"role": "user", "content": "Keep this"}], project_id="office-kit")
    reopened = VaultCatalog(path)
    assert reopened.list_projects()[0]["project_id"] == "office-kit"
    assert reopened.list_conversations("office-kit")[0]["title"] == "Office Kit"


def test_same_transcript_from_different_providers_is_cross_linked(tmp_path):
    vault = VaultCatalog(tmp_path / "vault")
    vault.register_project("dgm-mat", "DGM-MAT")
    messages = [{"id": "m1", "role": "user", "content": "Recover the DGM-MAT context"}]
    first = vault.archive_conversation(
        provider="chatgpt", conversation_id="chat-1", title="DGM-MAT",
        messages=messages, project_id="dgm-mat",
    )
    second = vault.archive_conversation(
        provider="gemini", conversation_id="gem-9", title="Different title",
        messages=messages, project_id="dgm-mat",
    )
    assert first["status"] == "archived"
    assert second["status"] == "archived_duplicate"
    assert second["duplicate"] is True
    assert second["canonical_provider"] == "chatgpt"
    assert Path(second["archive_path"]).is_file()
    assert len(vault.list_conversations("dgm-mat")) == 2
    assert vault.summary()["conversations"] == 2
    assert vault.summary()["duplicate_candidates"] == 1


def test_message_and_code_duplicates_are_indexed_without_deleting_sources(tmp_path):
    vault = VaultCatalog(tmp_path / "vault")
    vault.register_project("dgm-mat", "DGM-MAT")
    first = vault.archive_conversation(
        provider="chatgpt", conversation_id="one", title="DGM-MAT first",
        messages=[
            {"id": "m1", "role": "user", "content": "Shared requirement"},
            {"id": "m2", "role": "assistant", "content": "First answer"},
        ],
        artifacts=[{"artifact_id": "code-1", "language": "python", "code": "print('same code')"}],
        project_id="dgm-mat",
    )
    second = vault.archive_conversation(
        provider="gemini", conversation_id="two", title="DGM-MAT second",
        messages=[
            {"id": "m9", "role": "user", "content": "Shared requirement"},
            {"id": "m10", "role": "assistant", "content": "Different answer"},
        ],
        artifacts=[{"artifact_id": "code-2", "language": "python", "code": "print('same code')"}],
        project_id="dgm-mat",
    )
    assert first["status"] == "archived"
    assert second["status"] == "archived"
    assert len(vault.list_messages()) == 4
    assert len(vault.list_duplicate_messages()) == 1
    assert len(vault.list_duplicate_code()) == 1
    assert Path(first["archive_path"]).is_file()
    assert Path(second["archive_path"]).is_file()


def test_vault_refuses_to_live_inside_a_git_worktree(tmp_path):
    worktree = tmp_path / "repo"
    worktree.mkdir()
    (worktree / ".git").write_text("gitdir: ../git-metadata", encoding="utf-8")
    with pytest.raises(ValueError, match="outside every Git worktree"):
        VaultCatalog(worktree / "private-vault")
    assert not (worktree / "private-vault").exists()


def test_empty_captures_are_not_cross_provider_duplicates_and_whitespace_is_normalized(tmp_path):
    vault = VaultCatalog(tmp_path / "vault")
    vault.register_project("dgm-mat", "DGM-MAT")

    empty_chatgpt = vault.archive_conversation(
        provider="chatgpt", conversation_id="empty-1", title="Untitled", messages=[],
        project_id="dgm-mat",
    )
    empty_gemini = vault.archive_conversation(
        provider="gemini", conversation_id="empty-2", title="Untitled", messages=[],
        project_id="dgm-mat",
    )
    assert empty_chatgpt["status"] == "archived"
    assert empty_gemini["status"] == "archived"
    assert len(vault.list_conversations("dgm-mat")) == 2

    first = vault.archive_conversation(
        provider="chatgpt", conversation_id="text-1", title="Whitespace",
        messages=[{"id": "1", "role": "user", "content": "Hello   world"}],
        project_id="dgm-mat",
    )
    second = vault.archive_conversation(
        provider="gemini", conversation_id="text-2", title="Whitespace",
        messages=[{"id": "2", "role": "user", "content": "Hello world"}],
        project_id="dgm-mat",
    )
    assert first["status"] == "archived"
    assert second["status"] == "archived_duplicate"
    assert second["duplicate"] is True
    assert second["canonical_provider"] == "chatgpt"
    assert Path(second["archive_path"]).is_file()
    assert len(vault.list_conversations("dgm-mat")) == 4
    assert vault.summary()["duplicate_candidates"] == 1


def test_raw_browser_capture_is_immutable_and_idempotent(tmp_path):
    vault = VaultCatalog(tmp_path / "vault")
    first = vault.archive_raw_capture(
        provider="chatgpt", source_id="conversation-1", raw_bytes=b'{"messages":[1]}'
    )
    second = vault.archive_raw_capture(
        provider="chatgpt", source_id="conversation-1", raw_bytes=b'{"messages":[1]}'
    )
    assert first["status"] == "archived"
    assert second["status"] == "duplicate"
    assert first["sha256"] == second["sha256"]
    assert Path(first["archive_path"]).read_bytes() == b'{"messages":[1]}'


def test_default_vault_root_is_per_user_and_outside_the_repository(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "AppData" / "Local"))
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    monkeypatch.delenv("DGM_VAULT_PATH", raising=False)
    assert VaultCatalog.default_root() == (tmp_path / "AppData" / "Local" / "DGM-MAT" / "Vault").resolve()


def test_vault_root_override_is_shared_with_runtime_storage(tmp_path, monkeypatch):
    override = tmp_path / "external-vault"
    monkeypatch.setenv("DGM_VAULT_PATH", str(override))
    assert VaultCatalog.default_root() == override.resolve()


def test_older_build_refuses_to_downgrade_a_newer_vault_schema(tmp_path):
    vault = VaultCatalog(tmp_path / "vault")
    with sqlite3.connect(vault.database_path) as db:
        db.execute("UPDATE schema_meta SET value='999' WHERE key='schema_version'")
    with pytest.raises(RuntimeError, match="refusing to downgrade"):
        VaultCatalog(tmp_path / "vault")
    with sqlite3.connect(vault.database_path) as db:
        version = db.execute(
            "SELECT value FROM schema_meta WHERE key='schema_version'"
        ).fetchone()[0]
    assert version == "999"


def test_known_project_catalog_prefers_specific_alias_and_preserves_custom_metadata(tmp_path):
    vault = VaultCatalog(tmp_path / "vault")
    repository = tmp_path / "dgm-mat"
    repository.mkdir()
    vault.register_project(
        "dgm-mat", "DGM-MAT", repository_path=repository, aliases=["Custom DGM-MAT Alias"]
    )
    vault.register_known_projects()

    mobile = vault.suggest_project(
        "DGM-MAT Mobile — USB recovery",
        "The DGM-MAT Mobile backoffice APK must reconnect to its local brain.",
    )
    assert mobile["project_id"] == "dgm-mat-mobile"
    assert "DGM-MAT Mobile" in mobile["candidates"][0]["strongest_aliases"]

    dgm = vault.get_project("dgm-mat")
    assert "Custom DGM-MAT Alias" in dgm["aliases"]
    assert dgm["repository_path"] == str(repository.resolve())
    assert len(vault.list_projects()) == 9


def test_project_title_evidence_outweighs_incidental_mentions_and_ties_quarantine(tmp_path):
    vault = VaultCatalog(tmp_path / "vault")
    vault.register_known_projects()

    title_match = vault.suggest_project(
        "DGM-MAT Fixing — browser recovery",
        "The discussion also compares a DGM-HUB meeting flow.",
    )
    assert title_match["project_id"] == "dgm-mat"
    assert title_match["candidates"][0]["evidence_source"] == "title"

    ambiguous = vault.suggest_project(
        "General architecture review",
        "Compare DGM-MAT and DGM-HUB; both projects are equally central.",
    )
    assert ambiguous["project_id"] is None
    assert ambiguous["status"] == "ambiguous"
