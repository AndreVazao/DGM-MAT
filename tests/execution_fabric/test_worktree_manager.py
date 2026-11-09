from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from core.execution.execution_engine import ExecutionEngine
from core.execution.worktree_manager import WorktreeError, WorktreeManager


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
    return result.stdout.rstrip()


def make_repo(path: Path) -> Path:
    path.mkdir(parents=True)
    subprocess.run(["git", "init", "-b", "main", str(path)], check=True, capture_output=True)
    git(path, "config", "user.name", "DGM Test")
    git(path, "config", "user.email", "dgm-test@example.invalid")
    (path / "README.md").write_text("baseline\n", encoding="utf-8")
    git(path, "add", "README.md")
    git(path, "commit", "-m", "initial")
    return path.resolve()


def make_manager(repo: Path, base: Path) -> WorktreeManager:
    return WorktreeManager(base_path=base, repo_root=repo)


def test_create_worktree_creates_isolated_branch_and_preserves_primary_checkout(tmp_path):
    repo = make_repo(tmp_path / "repo")
    base = tmp_path / "worktrees"
    manager = make_manager(repo, base)

    target = manager.create_worktree("agent/coder/task-001", "task-001")

    assert target == (base / "task-001").resolve()
    assert git(target, "branch", "--show-current") == "agent/coder/task-001"
    assert git(target, "status", "--porcelain") == ""
    assert git(repo, "branch", "--show-current") == "main"
    assert git(repo, "status", "--porcelain") == ""
    assert (repo / "README.md").read_text(encoding="utf-8") == "baseline\n"


def test_create_worktree_is_idempotent_only_for_same_clean_task_pair(tmp_path):
    repo = make_repo(tmp_path / "repo")
    manager = make_manager(repo, tmp_path / "worktrees")

    first = manager.create_worktree("agent/coder/task-001", "task-001")
    second = manager.create_worktree("agent/coder/task-001", "task-001")

    assert first == second


def test_create_refuses_to_reuse_dirty_existing_worktree(tmp_path):
    repo = make_repo(tmp_path / "repo")
    manager = make_manager(repo, tmp_path / "worktrees")
    target = manager.create_worktree("agent/coder/task-001", "task-001")
    (target / "operator-notes.txt").write_text("preserve me\n", encoding="utf-8")

    with pytest.raises(WorktreeError, match="dirty"):
        manager.create_worktree("agent/coder/task-001", "task-001")

    assert (target / "operator-notes.txt").read_text(encoding="utf-8") == "preserve me\n"


def test_task_id_path_traversal_is_rejected(tmp_path):
    repo = make_repo(tmp_path / "repo")
    manager = make_manager(repo, tmp_path / "worktrees")

    with pytest.raises(WorktreeError, match="path-safe"):
        manager.create_worktree("agent/coder/task-001", "../outside")

    assert not (tmp_path / "outside").exists()


@pytest.mark.parametrize("branch", ["main", "develop", "release/v1", "production"])
def test_protected_branches_are_rejected(tmp_path, branch):
    repo = make_repo(tmp_path / "repo")
    manager = make_manager(repo, tmp_path / "worktrees")

    with pytest.raises(WorktreeError, match="Protected branch"):
        manager.create_worktree(branch, "task-001")


def test_invalid_git_branch_name_is_rejected(tmp_path):
    repo = make_repo(tmp_path / "repo")
    manager = make_manager(repo, tmp_path / "worktrees")

    with pytest.raises(WorktreeError, match="valid Git branch"):
        manager.create_worktree("agent/../main", "task-001")


def test_existing_branch_checked_out_elsewhere_is_not_shared(tmp_path):
    repo = make_repo(tmp_path / "repo")
    manager = make_manager(repo, tmp_path / "worktrees")
    existing = manager.create_worktree("agent/coder/task-001", "task-001")

    with pytest.raises(WorktreeError, match="already checked out"):
        manager.create_worktree("agent/coder/task-001", "task-002")

    assert existing.exists()


def test_cleanup_refuses_dirty_worktree_and_preserves_operator_data(tmp_path):
    repo = make_repo(tmp_path / "repo")
    manager = make_manager(repo, tmp_path / "worktrees")
    target = manager.create_worktree("agent/coder/task-001", "task-001")
    (target / "operator-notes.txt").write_text("preserve me\n", encoding="utf-8")

    with pytest.raises(WorktreeError, match="preserve recoverable work"):
        manager.cleanup_worktree("task-001")

    assert target.exists()
    assert (target / "operator-notes.txt").read_text(encoding="utf-8") == "preserve me\n"


def test_cleanup_refuses_ignored_files_instead_of_deleting_them(tmp_path):
    repo = make_repo(tmp_path / "repo")
    manager = make_manager(repo, tmp_path / "worktrees")
    target = manager.create_worktree("agent/coder/task-001", "task-001")
    git(target, "config", "core.excludesFile", str(tmp_path / "ignore-file"))
    (tmp_path / "ignore-file").write_text("ignored-local.txt\n", encoding="utf-8")
    (target / "ignored-local.txt").write_text("keep this too\n", encoding="utf-8")

    with pytest.raises(WorktreeError, match="ignored data"):
        manager.cleanup_worktree("task-001")

    assert (target / "ignored-local.txt").read_text(encoding="utf-8") == "keep this too\n"


def test_cleanup_removes_only_a_clean_registered_worktree(tmp_path):
    repo = make_repo(tmp_path / "repo")
    manager = make_manager(repo, tmp_path / "worktrees")
    target = manager.create_worktree("agent/coder/task-001", "task-001")

    assert manager.cleanup_worktree("task-001") is True
    assert not target.exists()
    assert git(repo, "branch", "--show-current") == "main"
    assert git(repo, "status", "--porcelain") == ""


def test_execution_engine_uses_the_correct_worktree_manager_contract(tmp_path):
    repo = make_repo(tmp_path / "repo")
    engine = ExecutionEngine(repo_root=repo, worktree_base_path=tmp_path / "worktrees")

    result = engine.start_execution("coder", "task-007")

    assert result["branch"] == "agent/coder/task-007"
    assert Path(result["path"]).is_dir()
    assert git(Path(result["path"]), "branch", "--show-current") == result["branch"]
    assert engine.cleanup_execution("task-007") is True


def test_cleanup_refuses_protected_branch_worktree_created_outside_manager(tmp_path):
    repo = make_repo(tmp_path / "repo")
    base = tmp_path / "worktrees"
    base.mkdir()
    target = base / "protected"
    git(repo, "worktree", "add", "-b", "develop", str(target), "HEAD")
    manager = make_manager(repo, base)

    with pytest.raises(WorktreeError, match="Protected branch"):
        manager.cleanup_worktree("protected")

    assert target.exists()
    assert git(target, "branch", "--show-current") == "develop"


def test_create_worktree_at_commit_pins_exact_sha_and_preserves_primary_head(tmp_path):
    repo = make_repo(tmp_path / "repo")
    first_sha = git(repo, "rev-parse", "HEAD")
    (repo / "README.md").write_text("second\n", encoding="utf-8")
    git(repo, "add", "README.md")
    git(repo, "commit", "-m", "second")
    primary_sha = git(repo, "rev-parse", "HEAD")
    manager = make_manager(repo, tmp_path / "worktrees")

    target = manager.create_worktree_at_commit(
        "agent/coder/pinned-001", "pinned-001", first_sha
    )

    assert git(target, "rev-parse", "HEAD") == first_sha
    assert git(repo, "rev-parse", "HEAD") == primary_sha
    assert git(target, "status", "--porcelain", "--untracked-files=all") == ""
    assert (target / "README.md").read_text(encoding="utf-8") == "baseline\n"


def test_create_worktree_at_commit_rejects_dirty_primary_checkout(tmp_path):
    repo = make_repo(tmp_path / "repo")
    commit_sha = git(repo, "rev-parse", "HEAD")
    (repo / "operator-data.txt").write_text("preserve\n", encoding="utf-8")
    manager = make_manager(repo, tmp_path / "worktrees")

    with pytest.raises(WorktreeError, match="Primary checkout is dirty"):
        manager.create_worktree_at_commit(
            "agent/coder/pinned-002", "pinned-002", commit_sha
        )

    assert (repo / "operator-data.txt").read_text(encoding="utf-8") == "preserve\n"
    assert not (tmp_path / "worktrees" / "pinned-002").exists()


@pytest.mark.parametrize("commit_sha", ["HEAD", "abc123", "../outside", "", "g" * 40])
def test_create_worktree_at_commit_rejects_non_full_object_ids(tmp_path, commit_sha):
    repo = make_repo(tmp_path / "repo")
    manager = make_manager(repo, tmp_path / "worktrees")

    with pytest.raises(WorktreeError, match="full 40- or 64-character"):
        manager.create_worktree_at_commit(
            "agent/coder/pinned-003", "pinned-003", commit_sha
        )


def test_create_worktree_at_commit_refuses_to_reuse_different_pin(tmp_path):
    repo = make_repo(tmp_path / "repo")
    first_sha = git(repo, "rev-parse", "HEAD")
    (repo / "README.md").write_text("second\n", encoding="utf-8")
    git(repo, "add", "README.md")
    git(repo, "commit", "-m", "second")
    second_sha = git(repo, "rev-parse", "HEAD")
    manager = make_manager(repo, tmp_path / "worktrees")
    manager.create_worktree_at_commit("agent/coder/pinned-004", "pinned-004", first_sha)

    with pytest.raises(WorktreeError, match="different commit"):
        manager.create_worktree_at_commit("agent/coder/pinned-004", "pinned-004", second_sha)
