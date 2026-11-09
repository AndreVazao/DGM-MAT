from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from core.repository_intelligence.branch_recovery_analyzer import (
    BranchRecoveryAnalyzer,
    BranchRecoveryAuditError,
)


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def commit_file(repo: Path, path: str, content: str, message: str) -> str:
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    git(repo, "add", path)
    git(repo, "commit", "-m", message)
    return git(repo, "rev-parse", "HEAD")


def make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.name", "Test")
    git(repo, "config", "user.email", "test@example.com")
    commit_file(repo, "README.md", "baseline\n", "baseline")
    return repo


def test_audit_reports_unique_branch_commits_and_changed_files(tmp_path):
    repo = make_repo(tmp_path)
    git(repo, "checkout", "-b", "legacy/feature")
    commit_file(repo, "core/feature.py", "print('feature')\n", "add feature")
    git(repo, "checkout", "main")

    result = BranchRecoveryAnalyzer().audit_repository(repo, "main")
    item = result["branches"][0]
    assert item["branch"] == "legacy/feature"
    assert item["status"] == "AHEAD"
    assert item["ahead_commits"] == 1
    assert item["behind_commits"] == 0
    assert item["changed_files_vs_default"] == [{"status": "A", "path": "core/feature.py"}]
    assert item["recommendation"] == "PRESERVE_AND_REVIEW_UNIQUE_WORK"
    assert result["read_only"] is True
    assert result["mutations_performed"] == []


def test_audit_identifies_branch_already_integrated(tmp_path):
    repo = make_repo(tmp_path)
    git(repo, "checkout", "-b", "legacy/integrated")
    commit_file(repo, "docs/old.md", "old\n", "add old docs")
    git(repo, "checkout", "main")
    git(repo, "merge", "--no-ff", "legacy/integrated", "-m", "integrate legacy")
    result = BranchRecoveryAnalyzer().audit_repository(repo, "main")
    item = result["branches"][0]
    assert item["already_integrated"] is True
    assert item["recommendation"] == "ALREADY_INTEGRATED_REVIEW_FOR_ARCHIVE"


def test_audit_classifies_diverged_branch_and_preserves_dirty_paths(tmp_path):
    repo = make_repo(tmp_path)
    git(repo, "checkout", "-b", "legacy/diverged")
    commit_file(repo, "legacy.txt", "legacy\n", "legacy work")
    git(repo, "checkout", "main")
    commit_file(repo, "current.txt", "current\n", "current work")
    (repo / "untracked.txt").write_text("untracked\n", encoding="utf-8")
    result = BranchRecoveryAnalyzer().audit_repository(repo, "main")
    item = result["branches"][0]
    assert item["status"] == "DIVERGED"
    assert item["ahead_commits"] == 1
    assert item["behind_commits"] == 1
    assert item["recommendation"] == "PRESERVE_AND_RECONCILE_FILE_BY_FILE"
    assert result["working_tree_dirty"] is True
    assert "untracked.txt" in result["working_tree_paths"]


def test_remote_comparison_refuses_to_guess_when_remote_object_missing(tmp_path):
    repo = make_repo(tmp_path)
    result = BranchRecoveryAnalyzer().compare_remote_branch(
        repo, local_branch="main", remote_sha="f" * 40,
    )
    assert result["status"] == "REMOTE_OBJECT_NOT_LOCAL"
    assert result["ahead"] is None
    assert result["behind"] is None


def test_remote_comparison_uses_objects_already_present(tmp_path):
    repo = make_repo(tmp_path)
    git(repo, "checkout", "-b", "remote-snapshot")
    remote_sha = commit_file(repo, "remote.txt", "remote\n", "remote change")
    git(repo, "checkout", "main")
    result = BranchRecoveryAnalyzer().compare_remote_branch(
        repo, local_branch="main", remote_sha=remote_sha,
    )
    assert result["status"] == "REMOTE_AHEAD"
    assert result["ahead"] == 0
    assert result["behind"] == 1
    assert result["changed_files"] == [{"status": "A", "path": "remote.txt"}]


def test_audit_rejects_invalid_branch_and_never_changes_refs(tmp_path):
    repo = make_repo(tmp_path)
    before = git(repo, "show-ref")
    with pytest.raises(BranchRecoveryAuditError):
        BranchRecoveryAnalyzer().audit_repository(repo, "../main")
    BranchRecoveryAnalyzer().audit_repository(repo, "main")
    assert git(repo, "show-ref") == before


def test_audit_requires_existing_default_branch(tmp_path):
    repo = make_repo(tmp_path)
    with pytest.raises(BranchRecoveryAuditError):
        BranchRecoveryAnalyzer().audit_repository(repo, "missing")
