from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from core.execution_fabric.safe_patch_engine import SafePatchEngine, SecurityError


PATCH = """diff --git a/readme.txt b/readme.txt
--- a/readme.txt
+++ b/readme.txt
@@ -1 +1 @@
-before
+after
"""


def git(path: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(path), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
        shell=False,
    )
    return result.stdout.strip()


def make_repo(path: Path, *, branch: str = "main") -> Path:
    path.mkdir(parents=True)
    subprocess.run(["git", "init", "-b", branch, str(path)], check=True, capture_output=True)
    git(path, "config", "user.name", "DGM Test")
    git(path, "config", "user.email", "dgm-test@example.invalid")
    (path / "readme.txt").write_text("before\n", encoding="utf-8")
    git(path, "add", "readme.txt")
    git(path, "commit", "-m", "initial")
    return path.resolve()


def make_worktree(repo: Path, path: Path, branch: str = "agent/task-1") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    git(repo, "worktree", "add", "-b", branch, str(path), "HEAD")
    return path.resolve()


def test_patch_is_applied_only_to_explicit_isolated_worktree(tmp_path):
    repo = make_repo(tmp_path / "repo")
    target = make_worktree(repo, tmp_path / "worktrees" / "task-1")

    result = SafePatchEngine().apply_patch(PATCH, target, repo)

    assert result["applied"] is True
    assert result["branch"] == "agent/task-1"
    assert result["changed_files"] == ["readme.txt"]
    assert (target / "readme.txt").read_text(encoding="utf-8") == "after\n"
    assert (repo / "readme.txt").read_text(encoding="utf-8") == "before\n"
    assert git(repo, "status", "--porcelain") == ""
    assert git(target, "status", "--porcelain")


def test_legacy_one_argument_apply_is_rejected(tmp_path):
    repo = make_repo(tmp_path / "repo")

    with pytest.raises(SecurityError, match="explicit isolated worktree"):
        SafePatchEngine().apply_patch(PATCH)

    assert (repo / "readme.txt").read_text(encoding="utf-8") == "before\n"


def test_primary_repository_is_never_a_patch_destination(tmp_path):
    repo = make_repo(tmp_path / "repo")

    with pytest.raises(SecurityError, match="primary repository"):
        SafePatchEngine().apply_patch(PATCH, repo, repo)

    assert (repo / "readme.txt").read_text(encoding="utf-8") == "before\n"


def test_patch_destination_must_belong_to_expected_repository(tmp_path):
    repo = make_repo(tmp_path / "repo")
    foreign = make_repo(tmp_path / "foreign")
    target = make_worktree(foreign, tmp_path / "foreign-worktrees" / "task-1")

    with pytest.raises(SecurityError, match="not a worktree of the expected repository"):
        SafePatchEngine().apply_patch(PATCH, target, repo)

    assert (target / "readme.txt").read_text(encoding="utf-8") == "before\n"


def test_dirty_target_worktree_is_rejected(tmp_path):
    repo = make_repo(tmp_path / "repo")
    target = make_worktree(repo, tmp_path / "worktrees" / "task-1")
    (target / "untracked.txt").write_text("keep me\n", encoding="utf-8")

    with pytest.raises(SecurityError, match="must be clean"):
        SafePatchEngine().apply_patch(PATCH, target, repo)

    assert (target / "readme.txt").read_text(encoding="utf-8") == "before\n"
    assert (target / "untracked.txt").read_text(encoding="utf-8") == "keep me\n"


@pytest.mark.parametrize("branch", ["develop", "release/v1", "production"])
def test_protected_branch_worktree_is_rejected(tmp_path, branch):
    repo = make_repo(tmp_path / "repo")
    target_name = branch.replace("/", "_")
    target = make_worktree(repo, tmp_path / "worktrees" / target_name, branch)

    with pytest.raises(SecurityError, match="Protected branch"):
        SafePatchEngine().apply_patch(PATCH, target, repo)

    assert (target / "readme.txt").read_text(encoding="utf-8") == "before\n"


def test_invalid_patch_is_rejected_without_modifying_worktree(tmp_path):
    repo = make_repo(tmp_path / "repo")
    target = make_worktree(repo, tmp_path / "worktrees" / "task-1")
    invalid = PATCH.replace("-before", "-not-the-current-content")

    with pytest.raises(SecurityError, match="Patch validation failed"):
        SafePatchEngine().apply_patch(invalid, target, repo)

    assert (target / "readme.txt").read_text(encoding="utf-8") == "before\n"


def test_destructive_patch_pattern_is_rejected(tmp_path):
    repo = make_repo(tmp_path / "repo")
    target = make_worktree(repo, tmp_path / "worktrees" / "task-1")
    destructive = PATCH.replace("+after", '+import os\n+os.system("format C:")')

    with pytest.raises(SecurityError, match="Destructive patch"):
        SafePatchEngine().apply_patch(destructive, target, repo)

    assert (target / "readme.txt").read_text(encoding="utf-8") == "before\n"


def test_path_traversal_patch_is_rejected_by_git_apply(tmp_path):
    repo = make_repo(tmp_path / "repo")
    target = make_worktree(repo, tmp_path / "worktrees" / "task-1")
    traversal = """diff --git a/../../outside.txt b/../../outside.txt
--- a/../../outside.txt
+++ b/../../outside.txt
@@ -0,0 +1 @@
+outside
"""

    with pytest.raises(SecurityError):
        SafePatchEngine().apply_patch(traversal, target, repo)

    assert not (tmp_path / "outside.txt").exists()
    assert (target / "readme.txt").read_text(encoding="utf-8") == "before\n"


def test_patch_size_limit_is_enforced(tmp_path):
    repo = make_repo(tmp_path / "repo")
    target = make_worktree(repo, tmp_path / "worktrees" / "task-1")
    oversized = PATCH + (" " * (SafePatchEngine.MAX_PATCH_BYTES + 1))

    with pytest.raises(SecurityError, match="512 KB"):
        SafePatchEngine().apply_patch(oversized, target, repo)

    assert (target / "readme.txt").read_text(encoding="utf-8") == "before\n"
