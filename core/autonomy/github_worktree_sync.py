"""Governed, non-destructive synchronization of DGM-MAT GitHub main.

The service never updates the authoritative checkout. It fetches one fixed
GitHub branch and materializes it in a dedicated detached worktree.
"""
from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Any, Callable


class GitHubWorktreeSyncError(RuntimeError):
    """Raised when GitHub sync cannot be completed without risking local work."""


class GitHubWorktreeSync:
    REMOTE_NAME = "origin"
    REMOTE_BRANCH = "main"
    WORKTREE_NAME = "dgm-mat-github-main-sync"
    EXPECTED_REMOTE_URL = "https://github.com/AndreVazao/DGM-MAT.git"

    def __init__(
        self,
        repo_root: str | Path,
        *,
        runner: Callable[..., Any] = subprocess.run,
        timeout_seconds: float = 120.0,
        expected_remote_url: str | None = None,
    ) -> None:
        self.repo_root = Path(repo_root).resolve(strict=False)
        self.worktrees_root = self.repo_root.parent / "_worktrees"
        self.target_path = self.worktrees_root / self.WORKTREE_NAME
        self.runner = runner
        self.timeout_seconds = timeout_seconds
        self.expected_remote_url = expected_remote_url or self.EXPECTED_REMOTE_URL
        self.command_count = 0
        if timeout_seconds <= 0 or timeout_seconds > 300:
            raise ValueError("timeout_seconds must be in (0, 300].")

    def _git(self, args: list[str], *, cwd: Path | None = None, allow_failure: bool = False) -> str:
        command = ["git", "-C", str(cwd or self.repo_root), *args]
        self.command_count += 1
        try:
            completed = self.runner(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout_seconds,
                check=False,
                shell=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise GitHubWorktreeSyncError(
                f"Git command failed to start or timed out: {args[0]}"
            ) from exc
        output = (completed.stdout or "").strip()
        if completed.returncode != 0 and not allow_failure:
            detail = (completed.stderr or output or "unknown Git error").strip()[:800]
            raise GitHubWorktreeSyncError(
                f"Git {args[0]} failed with exit code {completed.returncode}: {detail}"
            )
        return output

    @staticmethod
    def _normal_path(value: str | Path) -> str:
        return str(Path(value).resolve(strict=False)).replace("\\", "/").rstrip("/").casefold()

    def _registered_worktrees(self) -> set[str]:
        listing = self._git(["worktree", "list", "--porcelain"])
        registered: set[str] = set()
        for line in listing.splitlines():
            if line.startswith("worktree "):
                registered.add(self._normal_path(line[len("worktree "):]))
        return registered

    def sync(self) -> dict[str, Any]:
        started = time.monotonic()
        if not self.repo_root.is_dir() or not (self.repo_root / ".git").exists():
            raise GitHubWorktreeSyncError("Authoritative DGM-MAT root is not a Git working tree.")
        if not self.worktrees_root.is_dir():
            raise GitHubWorktreeSyncError("The approved DGM-MAT worktrees directory does not exist.")
        if self.worktrees_root.is_symlink():
            raise GitHubWorktreeSyncError("The approved worktrees directory must not be a symlink.")

        # git -C is pinned to repo_root; an empty prefix proves it is the root.
        if self._git(["rev-parse", "--show-prefix"]):
            raise GitHubWorktreeSyncError("Git repository identity does not match the expected DGM-MAT root.")

        remote_url = self._git(["remote", "get-url", self.REMOTE_NAME])
        normalized_remote = remote_url.replace(chr(92), "/").rstrip("/").casefold()
        normalized_expected = self.expected_remote_url.replace(chr(92), "/").rstrip("/").casefold()
        if normalized_remote != normalized_expected:
            raise GitHubWorktreeSyncError("origin URL does not match the approved DGM-MAT GitHub repository.")

        authoritative_head_before = self._git(["rev-parse", "HEAD"])
        authoritative_status_before = self._git(["status", "--porcelain=v1", "--untracked-files=all"])

        # Fetch only the fixed main branch. No user-supplied remote/refspec and no prune.
        self._git([
            "fetch", "--no-tags", self.REMOTE_NAME,
            "refs/heads/main:refs/remotes/origin/main",
        ])
        remote_sha = self._git(["rev-parse", "refs/remotes/origin/main"])

        registered = self._registered_worktrees()
        target_key = self._normal_path(self.target_path)
        target_exists = self.target_path.exists()
        target_registered = target_key in registered

        if target_exists and not target_registered:
            raise GitHubWorktreeSyncError(
                "The dedicated sync path exists but is not registered as a Git worktree; refusing to adopt or overwrite it."
            )
        if target_registered and not target_exists:
            raise GitHubWorktreeSyncError(
                "Git registers the dedicated sync worktree but its directory is missing; refusing implicit repair."
            )

        created = False
        if target_exists:
            target_status = self._git(
                ["status", "--porcelain=v1", "--untracked-files=all"],
                cwd=self.target_path,
            )
            if target_status:
                raise GitHubWorktreeSyncError(
                    "The existing GitHub sync worktree is dirty; refusing to overwrite local work."
                )
            target_head = self._git(["rev-parse", "HEAD"], cwd=self.target_path)
            if target_head != remote_sha:
                raise GitHubWorktreeSyncError(
                    "The existing sync worktree does not match the newly fetched origin/main; manual review is required."
                )
        else:
            self._git([
                "worktree", "add", "--detach", str(self.target_path),
                "refs/remotes/origin/main",
            ])
            created = True
            target_head = self._git(["rev-parse", "HEAD"], cwd=self.target_path)

        target_prefix = self._git(["rev-parse", "--show-prefix"], cwd=self.target_path)
        target_status = self._git(
            ["status", "--porcelain=v1", "--untracked-files=all"],
            cwd=self.target_path,
        )
        target_head = self._git(["rev-parse", "HEAD"], cwd=self.target_path)
        target_branch = self._git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=self.target_path)

        authoritative_head_after = self._git(["rev-parse", "HEAD"])
        authoritative_status_after = self._git(["status", "--porcelain=v1", "--untracked-files=all"])
        if (
            authoritative_head_after != authoritative_head_before
            or authoritative_status_after != authoritative_status_before
        ):
            raise GitHubWorktreeSyncError(
                "Authoritative checkout changed during sync; result cannot be certified."
            )
        if target_prefix:
            raise GitHubWorktreeSyncError("The resulting worktree top-level path failed verification.")
        if target_status or target_head != remote_sha:
            raise GitHubWorktreeSyncError("The resulting worktree failed clean-state or commit verification.")
        if target_branch != "HEAD":
            raise GitHubWorktreeSyncError("The resulting worktree is not detached; refusing branch mutation.")

        return {
            "status": "completed",
            "repository": "AndreVazao/DGM-MAT",
            "remote": self.REMOTE_NAME,
            "branch": self.REMOTE_BRANCH,
            "remote_url": remote_url,
            "remote_sha": remote_sha,
            "worktree_path": str(self.target_path),
            "worktree_sha": target_head,
            "worktree_created": created,
            "worktree_clean": not bool(target_status),
            "worktree_detached": target_branch == "HEAD",
            "git_commands_executed": self.command_count,
            "authoritative_head_unchanged": authoritative_head_after == authoritative_head_before,
            "authoritative_worktree_unchanged": authoritative_status_after == authoritative_status_before,
            "authoritative_head": authoritative_head_after,
            "authoritative_dirty_entries": len(authoritative_status_after.splitlines()) if authoritative_status_after else 0,
            "fetch_scope": "fixed origin/main ref only; no prune",
            "mutations": ["Git remote-tracking ref update", "dedicated detached worktree creation"] if created else ["Git remote-tracking ref update"],
            "forbidden_operations_used": [],
            "duration_seconds": round(time.monotonic() - started, 3),
        }
