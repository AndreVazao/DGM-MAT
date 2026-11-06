import json
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
    assert second["status"] == "duplicate"
    assert second["canonical_provider"] == "chatgpt"
    assert vault.summary()["conversations"] == 1
    assert vault.summary()["duplicate_candidates"] == 1
