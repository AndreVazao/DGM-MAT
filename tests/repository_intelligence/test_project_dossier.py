from __future__ import annotations

from pathlib import Path

import pytest

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
    assert dossier["repository"]["snapshots"][0]["tree_fingerprint"] == snapshot["tree_fingerprint"]
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
