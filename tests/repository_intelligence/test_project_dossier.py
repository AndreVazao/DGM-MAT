from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import HTTPException

from core.repository_intelligence.project_dossier import ProjectDossierError, build_project_dossier
from core.repository_intelligence.static_audit import audit_project
from core.vault.catalog import VaultCatalog


def _vault(tmp_path: Path):
    root = tmp_path / "vault"
    vault = VaultCatalog(vault_root=root)
    repo = tmp_path / "sample-repo"
    repo.mkdir()
    (repo / "main.py").write_text("def main():\n    return 1\n", encoding="utf-8")
    vault.register_project("sample", "Sample Project", repo, aliases=["Sample"])
    return vault, repo


def test_project_dossier_returns_only_bounded_metadata_not_transcript_body(tmp_path: Path):
    vault, repo = _vault(tmp_path)
    vault.archive_conversation(
        provider="chatgpt",
        conversation_id="conversation-1",
        title="Project planning",
        messages=[{"id": "message-1", "role": "user", "content": "private transcript body"}],
        content="private transcript body",
        completeness="complete",
        project_id="sample",
        assignment_evidence=["operator_mapping"],
    )

    dossier = build_project_dossier(vault=vault, project_id="sample")

    assert dossier["schema"] == "dgm-mat.project-dossier.v1"
    assert dossier["project"]["project_id"] == "sample"
    assert dossier["coverage"]["vault_conversations_total"] == 1
    assert dossier["coverage"]["by_provider"] == {"chatgpt": 1}
    assert dossier["conversations"][0]["evidence_ref"] == "chatgpt:conversation-1"
    assert dossier["conversations"][0]["assignment_status"]
    assert "private transcript body" not in str(dossier)
    assert dossier["status"]["operator_decisions"] == "not_inferred_from_conversation_text"
    assert dossier["read_only"] is True


def test_project_dossier_includes_latest_snapshot_and_static_audit(tmp_path: Path):
    vault, repo = _vault(tmp_path)
    snapshot = vault.snapshot_repository("sample", repo)
    audit = audit_project(vault=vault, project_id="sample")

    dossier = build_project_dossier(vault=vault, project_id="sample")

    assert dossier["repository"]["snapshots"][0]["snapshot_id"] == snapshot["snapshot_id"]
    assert dossier["repository"]["snapshots"][0]["tree_fingerprint"] == snapshot["fingerprint"]
    assert dossier["static_audit"]["audit_fingerprint"] == audit["audit_fingerprint"]
    assert dossier["static_audit"]["summary"]["python_files"] == 1
    assert dossier["status"]["classification"] == "evidence_partial"


def test_project_dossier_rejects_unknown_project_and_unbounded_limits(tmp_path: Path):
    vault, _ = _vault(tmp_path)
    with pytest.raises(ProjectDossierError, match="Unknown Vault project"):
        build_project_dossier(vault=vault, project_id="missing")
    with pytest.raises(ProjectDossierError, match="bounds"):
        build_project_dossier(vault=vault, project_id="sample", conversation_limit=10000)


def test_project_dossier_reports_unknown_provider_completeness_instead_of_claiming_full_coverage(tmp_path: Path):
    vault, _ = _vault(tmp_path)
    dossier = build_project_dossier(vault=vault, project_id="sample")
    assert dossier["coverage"]["provider_archive_completeness"] == "unknown"
    assert dossier["coverage"]["vault_conversations_total"] == 0
    assert dossier["status"]["classification"] == "no_evidence"


def test_project_dossier_api_uses_configured_vault_and_returns_read_only_projection(tmp_path: Path, monkeypatch):
    from core.api import repository_learning_api

    vault, repo = _vault(tmp_path)
    monkeypatch.setattr(VaultCatalog, "default_root", staticmethod(lambda: vault.root))
    monkeypatch.setattr(
        repository_learning_api.repository_learning_service,
        "list_repositories",
        lambda limit: [{
            "path": str(repo),
            "name": "sample-repo",
            "branch": "main",
            "head_sha": "e" * 40,
            "dirty": False,
            "scan_status": "complete",
            "scan_error": None,
            "last_seen_at": "2026-11-13T08:00:00+00:00",
            "scan_count": 1,
            "tree_path": None,
            "tree_sha256": None,
            "tree_entries": None,
            "tree_truncated": False,
            "tree_generated_at": None,
            "tree_error": None,
        }],
    )
    result = repository_learning_api.project_dossier(
        project_id="sample",
        conversation_limit=100,
        snapshot_limit=20,
        finding_limit=50,
    )
    assert result["schema"] == "dgm-mat.project-dossier.v1"
    assert result["read_only"] is True
    assert result["limitations"]
    assert result["repository"]["local_inventory"]["match_status"] == "exact_path_match"
    assert result["repository"]["local_inventory"]["repositories"][0]["head_sha"] == "e" * 40


def test_project_dossier_links_github_references_and_code_candidates_to_source_conversations(tmp_path: Path):
    vault, _ = _vault(tmp_path)
    vault.archive_conversation(
        provider="chatgpt",
        conversation_id="conversation-with-repo",
        title="Repository implementation",
        messages=[{
            "id": "message-42",
            "role": "assistant",
            "content": "Repository: https://github.com/example-org/example-project",
        }],
        content="Repository implementation details",
        completeness="complete",
        project_id="sample",
        artifacts=[{
            "artifact_id": "artifact-1",
            "language": "python",
            "code": "print('candidate')",
            "fingerprint": "candidate-fingerprint",
        }],
    )

    dossier = build_project_dossier(vault=vault, project_id="sample")

    refs = dossier["repository"]["conversation_linked_references"]
    assert len(refs) == 1
    assert refs[0]["url"] == "https://github.com/example-org/example-project"
    assert refs[0]["verification_status"] == "pending_verification"
    assert refs[0]["source"]["message_id"] == "message-42"

    artifacts = dossier["repository"]["conversation_linked_code_candidates"]
    assert len(artifacts) == 1
    assert artifacts[0]["artifact_id"] == "artifact-1"
    assert artifacts[0]["verification_status"] == "candidate_not_repository_verified"


def test_project_dossier_links_local_git_metadata_only_by_exact_repository_path(tmp_path: Path):
    vault, repo = _vault(tmp_path)
    inventory = [
        {
            "path": str(repo),
            "name": "sample-repo",
            "branch": "feature/recovery",
            "head_sha": "a" * 40,
            "dirty": True,
            "scan_status": "complete",
            "scan_error": None,
            "last_seen_at": "2026-11-13T08:00:00+00:00",
            "scan_count": 4,
            "tree_path": "/vault/trees/sample.tree.txt",
            "tree_sha256": "b" * 64,
            "tree_entries": 12,
            "tree_truncated": False,
            "tree_generated_at": "2026-11-13T08:00:00+00:00",
            "tree_error": None,
        },
        {
            "path": str(tmp_path / "another" / "sample-repo"),
            "name": "sample-repo",
            "branch": "wrong-match",
            "head_sha": "c" * 40,
            "dirty": False,
            "scan_status": "complete",
        },
    ]

    dossier = build_project_dossier(
        vault=vault,
        project_id="sample",
        repository_inventory=inventory,
    )

    local = dossier["repository"]["local_inventory"]
    assert local["match_status"] == "exact_path_match"
    assert len(local["repositories"]) == 1
    assert local["repositories"][0]["branch"] == "feature/recovery"
    assert local["repositories"][0]["head_sha"] == "a" * 40
    assert local["repositories"][0]["working_tree_dirty"] is True
    assert "not a live Git probe" in local["note"]


def test_project_dossier_does_not_infer_local_repository_from_similar_name(tmp_path: Path):
    vault, _repo = _vault(tmp_path)
    dossier = build_project_dossier(
        vault=vault,
        project_id="sample",
        repository_inventory=[{
            "path": str(tmp_path / "different" / "sample"),
            "name": "sample-repo",
            "branch": "main",
            "head_sha": "d" * 40,
            "dirty": False,
            "scan_status": "complete",
        }],
    )
    local = dossier["repository"]["local_inventory"]
    assert local["match_status"] == "no_exact_path_match"
    assert local["repositories"] == []


def test_natural_language_project_resolver_requires_whole_alias_matches(tmp_path: Path):
    from core.api.repository_learning_api import _resolve_project_query

    vault, _ = _vault(tmp_path)
    result = _resolve_project_query("Please show SAMPLE project status", vault.list_projects())
    assert result["status"] == "resolved"
    assert result["project"]["project_id"] == "sample"
    assert _resolve_project_query("samples are useful", vault.list_projects())["status"] == "not_found"


def test_natural_language_project_resolver_reports_multiple_projects_as_ambiguous(tmp_path: Path):
    from core.api.repository_learning_api import _resolve_project_query

    vault, _ = _vault(tmp_path)
    other_repo = tmp_path / "other-repo"
    other_repo.mkdir()
    vault.register_project("other", "Other Project", other_repo, aliases=["Other"])
    result = _resolve_project_query(
        "Compare Sample Project with Other",
        vault.list_projects(),
    )
    assert result["status"] == "ambiguous"
    assert {item["project_id"] for item in result["candidates"]} == {"sample", "other"}


def test_natural_language_dossier_api_returns_dossier_for_unique_project_alias(tmp_path: Path, monkeypatch):
    from core.api import repository_learning_api

    vault, _ = _vault(tmp_path)
    monkeypatch.setattr(VaultCatalog, "default_root", staticmethod(lambda: vault.root))
    monkeypatch.setattr(repository_learning_api.repository_learning_service, "list_repositories", lambda limit: [])
    result = repository_learning_api.project_dossier(
        project_id=None,
        query="What is the status of Sample Project?",
        conversation_limit=100,
        snapshot_limit=20,
        finding_limit=50,
    )
    assert result["resolution"]["status"] == "resolved"
    assert result["project"]["project_id"] == "sample"


def test_natural_language_dossier_api_returns_ambiguity_without_guessing(tmp_path: Path, monkeypatch):
    from core.api import repository_learning_api

    vault, _ = _vault(tmp_path)
    other_repo = tmp_path / "other-repo"
    other_repo.mkdir()
    vault.register_project("other", "Other Project", other_repo, aliases=["Other"])
    monkeypatch.setattr(VaultCatalog, "default_root", staticmethod(lambda: vault.root))
    result = repository_learning_api.project_dossier(
        project_id=None,
        query="Compare Sample Project with Other",
        conversation_limit=100,
        snapshot_limit=20,
        finding_limit=50,
    )
    assert result["status"] == "ambiguous"
    assert len(result["candidates"]) == 2


def test_project_dossier_api_requires_exactly_one_project_selector(tmp_path: Path, monkeypatch):
    from core.api import repository_learning_api

    vault, _ = _vault(tmp_path)
    monkeypatch.setattr(VaultCatalog, "default_root", staticmethod(lambda: vault.root))
    with pytest.raises(HTTPException) as exc:
        repository_learning_api.project_dossier(
            project_id=None,
            query=None,
            conversation_limit=100,
            snapshot_limit=20,
            finding_limit=50,
        )
    assert exc.value.status_code == 400
