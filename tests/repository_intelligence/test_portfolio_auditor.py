from pathlib import Path

from core.repository_intelligence.portfolio_auditor import RepositoryAuditEngine


def _git(repo: Path, *args: str) -> None:
    import subprocess
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def test_audit_reads_real_git_metadata(tmp_path):
    repo = tmp_path / "demo"
    repo.mkdir()
    (repo / "README.md").write_text("# Demo\nA small Python tool.", encoding="utf-8")
    (repo / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    (repo / "main.py").write_text("print('ok')\n", encoding="utf-8")
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "init")

    audit = RepositoryAuditEngine(tmp_path).audit_repository(repo)

    assert audit.has_git is True
    assert audit.commit_count == 1
    assert audit.branch
    assert audit.readme_present is True
    assert "pyproject.toml" in audit.manifests
    assert "Python" in audit.languages
    assert audit.dirty is False


def test_audit_marks_protected_mirror(tmp_path):
    repo = tmp_path / "DGM-MAT-FULL-MIRROR"
    repo.mkdir()
    _git(repo, "init")

    audit = RepositoryAuditEngine(tmp_path).audit_repository(repo)

    assert audit.protected is True
    assert audit.classification == "ARCHIVE"
    assert audit.recommended_action.startswith("AUDIT_ONLY")
