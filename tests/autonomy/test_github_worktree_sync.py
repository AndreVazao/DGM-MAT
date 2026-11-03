from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from core.autonomy.github_worktree_sync import GitHubWorktreeSync, GitHubWorktreeSyncError


def _git(cwd: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(cwd), *args],
        capture_output=True,
        text=True,
        check=False,
        shell=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    return (completed.stdout or "").strip()


def _repository(tmp_path: Path) -> tuple[Path, Path, Path]:
    origin = tmp_path / "origin.git"
    seed = tmp_path / "seed"
    repo = tmp_path / "DGM-MAT"
    subprocess.run(["git", "init", "--bare", "--initial-branch=main", str(origin)], check=True, capture_output=True)
    subprocess.run(["git", "init", "--initial-branch=main", str(seed)], check=True, capture_output=True)
    _git(seed, "config", "user.name", "DGM Test")
    _git(seed, "config", "user.email", "dgm-test@example.invalid")
    (seed / "README.md").write_text("initial\n", encoding="utf-8")
    _git(seed, "add", "README.md")
    _git(seed, "commit", "-m", "initial")
    origin_url = origin.as_uri()
    _git(seed, "remote", "add", "origin", origin_url)
    _git(seed, "push", "-u", "origin", "main")
    subprocess.run(["git", "clone", "--branch", "main", origin_url, str(repo)], check=True, capture_output=True)
    _git(repo, "config", "user.name", "DGM Test")
    _git(repo, "config", "user.email", "dgm-test@example.invalid")
    (tmp_path / "_worktrees").mkdir()
    return repo, origin, seed


def _service(repo: Path, origin: Path) -> GitHubWorktreeSync:
    return GitHubWorktreeSync(repo, expected_remote_url=origin.as_uri(), timeout_seconds=20)


def test_sync_creates_clean_detached_worktree_and_preserves_dirty_authoritative_checkout(tmp_path):
    repo, origin, _ = _repository(tmp_path)
    (repo / "README.md").write_text("local unsaved change\n", encoding="utf-8")
    (repo / "operator-notes.txt").write_text("must remain untouched\n", encoding="utf-8")
    before_head = _git(repo, "rev-parse", "HEAD")
    before_status = _git(repo, "status", "--porcelain=v1", "--untracked-files=all")

    result = _service(repo, origin).sync()

    assert result["status"] == "completed"
    assert result["worktree_created"] is True
    assert result["worktree_clean"] is True
    assert result["worktree_detached"] is True
    assert result["git_commands_executed"] >= 10
    assert result["authoritative_head_unchanged"] is True
    assert result["authoritative_worktree_unchanged"] is True
    assert result["remote_sha"] == result["worktree_sha"]
    assert _git(repo, "rev-parse", "HEAD") == before_head
    assert _git(repo, "status", "--porcelain=v1", "--untracked-files=all") == before_status
    assert (repo / "operator-notes.txt").read_text(encoding="utf-8") == "must remain untouched\n"
    assert _git(Path(result["worktree_path"]), "rev-parse", "--abbrev-ref", "HEAD") == "HEAD"


def test_sync_is_idempotent_when_existing_worktree_is_clean_and_current(tmp_path):
    repo, origin, _ = _repository(tmp_path)
    service = _service(repo, origin)

    first = service.sync()
    second = service.sync()

    assert first["worktree_created"] is True
    assert second["worktree_created"] is False
    assert second["remote_sha"] == first["remote_sha"]
    assert second["worktree_sha"] == first["worktree_sha"]
    assert second["worktree_clean"] is True


def test_sync_refuses_to_overwrite_dirty_existing_worktree(tmp_path):
    repo, origin, _ = _repository(tmp_path)
    service = _service(repo, origin)
    first = service.sync()
    target = Path(first["worktree_path"])
    (target / "local-review.txt").write_text("preserve me\n", encoding="utf-8")

    with pytest.raises(GitHubWorktreeSyncError, match="worktree is dirty"):
        service.sync()

    assert (target / "local-review.txt").read_text(encoding="utf-8") == "preserve me\n"


def test_sync_refuses_to_advance_existing_worktree_when_github_main_moves(tmp_path):
    repo, origin, seed = _repository(tmp_path)
    service = _service(repo, origin)
    first = service.sync()

    (seed / "README.md").write_text("remote advance\n", encoding="utf-8")
    _git(seed, "add", "README.md")
    _git(seed, "commit", "-m", "remote advance")
    _git(seed, "push", "origin", "main")

    with pytest.raises(GitHubWorktreeSyncError, match="does not match the newly fetched"):
        service.sync()

    assert _git(Path(first["worktree_path"]), "rev-parse", "HEAD") == first["worktree_sha"]


def test_sync_fails_closed_when_origin_fetch_fails(tmp_path):
    repo, origin, _ = _repository(tmp_path)
    missing = tmp_path / "missing-origin.git"
    _git(repo, "remote", "set-url", "origin", missing.as_uri())

    with pytest.raises(GitHubWorktreeSyncError, match="Git fetch failed"):
        GitHubWorktreeSync(repo, expected_remote_url=missing.as_uri(), timeout_seconds=20).sync()


def test_sync_rejects_unapproved_origin_identity(tmp_path):
    repo, origin, _ = _repository(tmp_path)

    with pytest.raises(GitHubWorktreeSyncError, match="origin URL does not match"):
        GitHubWorktreeSync(repo, expected_remote_url=(tmp_path / "other.git").as_uri()).sync()
