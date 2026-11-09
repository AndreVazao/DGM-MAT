from __future__ import annotations

import re
import subprocess
from pathlib import Path

from core.observability.logger import dgm_logger


class WorktreeError(RuntimeError):
    """Raised when a requested Git worktree cannot be safely created or removed."""


class WorktreeManager:
    """Create and retire task worktrees without touching the primary checkout."""

    PROTECTED_BRANCHES = frozenset({
        "main", "master", "develop", "release", "production", "stable", "trunk",
    })
    PROTECTED_PREFIXES = ("release/", "production/", "stable/")
    TASK_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")

    def __init__(
        self,
        base_path: str | Path = ".runtime/worktrees",
        *,
        repo_root: str | Path | None = None,
        timeout_seconds: int = 30,
    ) -> None:
        if not 1 <= timeout_seconds <= 120:
            raise ValueError("timeout_seconds must be between 1 and 120")
        self.timeout_seconds = timeout_seconds
        inferred_root = Path(repo_root).expanduser() if repo_root is not None else Path(__file__).resolve().parents[2]
        self.repo_root = inferred_root.resolve(strict=True)
        reported_root = Path(self._run_git(["rev-parse", "--show-toplevel"])).resolve(strict=True)
        if reported_root != self.repo_root:
            raise WorktreeError("repo_root must be the exact primary Git repository root.")

        configured_base = Path(base_path).expanduser()
        if not configured_base.is_absolute():
            configured_base = self.repo_root / configured_base
        configured_base.mkdir(parents=True, exist_ok=True)
        self.base_path = configured_base.resolve(strict=True)
        if not self.base_path.is_dir():
            raise WorktreeError("Worktree base path must be a directory.")
        self._common_git_dir = self._resolve_common_git_dir(self.repo_root)

    def _run_git(self, args: list[str], *, cwd: Path | None = None) -> str:
        location = cwd or self.repo_root
        try:
            result = subprocess.run(
                ["git", "-C", str(location), *args],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                shell=False,
                timeout=self.timeout_seconds,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise WorktreeError(f"Git operation failed: {type(exc).__name__}") from None
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "Git operation failed").strip()
            raise WorktreeError(detail[:240])
        return result.stdout.rstrip()

    def _resolve_common_git_dir(self, path: Path) -> Path:
        raw = self._run_git(["rev-parse", "--git-common-dir"], cwd=path).strip()
        common = Path(raw)
        if not common.is_absolute():
            common = path / common
        try:
            return common.resolve(strict=True)
        except (OSError, RuntimeError):
            raise WorktreeError("Git common directory cannot be resolved.") from None

    @classmethod
    def _validate_task_id(cls, task_id: str) -> str:
        if not isinstance(task_id, str) or not cls.TASK_ID_PATTERN.fullmatch(task_id):
            raise WorktreeError("task_id must be a 1-100 character path-safe identifier.")
        if task_id in {".", ".."}:
            raise WorktreeError("task_id cannot be a relative path segment.")
        return task_id

    @classmethod
    def _validate_branch(cls, branch: str) -> str:
        if not isinstance(branch, str) or not branch.strip():
            raise WorktreeError("A non-empty branch name is required.")
        normalized = branch.casefold()
        if normalized in cls.PROTECTED_BRANCHES or normalized.startswith(cls.PROTECTED_PREFIXES):
            raise WorktreeError(f"Protected branch '{branch}' cannot be used for task execution.")
        try:
            result = subprocess.run(
                ["git", "check-ref-format", "--branch", branch],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                shell=False,
                timeout=10,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise WorktreeError(f"Branch validation failed: {type(exc).__name__}") from None
        if result.returncode != 0:
            raise WorktreeError("Branch name is not a valid Git branch reference.")
        return branch

    def _target_path(self, task_id: str) -> Path:
        safe_id = self._validate_task_id(task_id)
        target = (self.base_path / safe_id).resolve(strict=False)
        if not target.is_relative_to(self.base_path) or target == self.base_path:
            raise WorktreeError("Resolved worktree path escaped its configured base directory.")
        return target

    def _registered_worktrees(self) -> dict[str, str]:
        output = self._run_git(["worktree", "list", "--porcelain"])
        result: dict[str, str] = {}
        current_path: str | None = None
        for line in output.splitlines():
            if line.startswith("worktree "):
                current_path = str(Path(line[len("worktree "):]).resolve(strict=False))
            elif line.startswith("branch ") and current_path:
                result[line[len("branch "):].removeprefix("refs/heads/")] = current_path
        return result

    def _validate_existing_target(self, target: Path, branch: str) -> Path:
        try:
            resolved = target.resolve(strict=True)
        except (OSError, RuntimeError):
            raise WorktreeError("Existing worktree path cannot be resolved.") from None
        if not resolved.is_dir():
            raise WorktreeError("Existing worktree path is not a directory.")
        root = Path(self._run_git(["rev-parse", "--show-toplevel"], cwd=resolved)).resolve(strict=True)
        if root != resolved:
            raise WorktreeError("Existing path is not an exact Git worktree root.")
        if self._resolve_common_git_dir(root) != self._common_git_dir:
            raise WorktreeError("Existing path belongs to a different Git repository.")
        actual_branch = self._run_git(["branch", "--show-current"], cwd=root).strip()
        if actual_branch != branch:
            raise WorktreeError("Existing worktree path is registered to a different branch.")
        registered_path = self._registered_worktrees().get(actual_branch)
        if not registered_path or Path(registered_path).resolve(strict=False) != root:
            raise WorktreeError("Existing path is not the registered location for this Git worktree.")
        if self._run_git(["status", "--porcelain", "--untracked-files=all"], cwd=root):
            raise WorktreeError("Existing task worktree is dirty; it will be preserved, not reused.")
        return root

    def create_worktree_at_commit(self, branch: str, task_id: str, commit_sha: str) -> Path:
        """Create a task worktree from one immutable commit SHA.

        The primary checkout must be clean. The supplied revision must be a
        full object ID resolving to a commit in this repository; moving refs
        and abbreviated hashes are deliberately rejected.
        """
        branch = self._validate_branch(branch)
        target = self._target_path(task_id)
        if not isinstance(commit_sha, str) or not re.fullmatch(r"(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})", commit_sha):
            raise WorktreeError("base commit must be a full 40- or 64-character Git object ID.")

        if self._run_git(["status", "--porcelain", "--untracked-files=all"], cwd=self.repo_root):
            raise WorktreeError("Primary checkout is dirty; pinned worktree creation refused.")

        resolved_commit = self._run_git(
            ["rev-parse", "--verify", "--end-of-options", f"{commit_sha}^{{commit}}"],
            cwd=self.repo_root,
        ).strip().lower()
        if resolved_commit != commit_sha.lower():
            raise WorktreeError("base commit did not resolve to the exact supplied commit SHA.")

        if target.exists():
            existing = self._validate_existing_target(target, branch)
            existing_sha = self._run_git(["rev-parse", "HEAD"], cwd=existing).strip().lower()
            if existing_sha != resolved_commit:
                raise WorktreeError("Existing worktree is pinned to a different commit; it will be preserved.")
            return existing

        checked_out = self._registered_worktrees().get(branch)
        if checked_out is not None:
            raise WorktreeError(
                f"Branch '{branch}' is already checked out at another worktree; refusing to share it."
            )
        if self._run_git(["branch", "--list", branch], cwd=self.repo_root).strip():
            raise WorktreeError("Task branch already exists; pinned worktree creation will not reuse it.")

        target.parent.mkdir(parents=True, exist_ok=True)
        self._run_git(
            ["worktree", "add", "-b", branch, str(target), resolved_commit],
            cwd=self.repo_root,
        )
        created = self._validate_existing_target(target, branch)
        actual_sha = self._run_git(["rev-parse", "HEAD"], cwd=created).strip().lower()
        if actual_sha != resolved_commit:
            raise WorktreeError("Created worktree HEAD does not match the approved base commit.")
        return created

    def create_worktree(self, branch: str, task_id: str) -> Path:
        """Create a task branch/worktree; reuse only the exact existing clean pair."""
        branch = self._validate_branch(branch)
        target = self._target_path(task_id)

        if target.exists():
            dgm_logger.info(f"WorktreeManager: Checking existing task worktree {target}")
            return self._validate_existing_target(target, branch)

        checked_out = self._registered_worktrees().get(branch)
        if checked_out is not None:
            raise WorktreeError(
                f"Branch '{branch}' is already checked out at another worktree; refusing to share it."
            )

        branch_list = self._run_git(["branch", "--list", branch], cwd=self.repo_root)
        branch_exists = bool(branch_list.strip())

        target.parent.mkdir(parents=True, exist_ok=True)
        if branch_exists:
            args = ["worktree", "add", str(target), branch]
        else:
            args = ["worktree", "add", "-b", branch, str(target), "HEAD"]

        dgm_logger.info(f"WorktreeManager: Creating isolated branch {branch} at {target}")
        self._run_git(args, cwd=self.repo_root)
        return self._validate_existing_target(target, branch)

    def cleanup_worktree(self, task_id: str) -> bool:
        """Remove only a clean registered task worktree; dirty state is retained."""
        target = self._target_path(task_id)
        if not target.exists():
            return False

        resolved = target.resolve(strict=True)
        root = Path(self._run_git(["rev-parse", "--show-toplevel"], cwd=resolved)).resolve(strict=True)
        if root != resolved or root == self.repo_root:
            raise WorktreeError("Cleanup target is not a separate registered task worktree.")
        if self._resolve_common_git_dir(root) != self._common_git_dir:
            raise WorktreeError("Cleanup target belongs to a different Git repository.")
        branch = self._run_git(["branch", "--show-current"], cwd=root).strip()
        self._validate_branch(branch)
        registered_path = self._registered_worktrees().get(branch)
        if not registered_path or Path(registered_path).resolve(strict=False) != root:
            raise WorktreeError("Cleanup target is not the registered location for this Git worktree.")
        status = self._run_git(["status", "--porcelain", "--untracked-files=all"], cwd=root)
        ignored_or_untracked = self._run_git(["clean", "-ndx"], cwd=root)
        if status or ignored_or_untracked:
            raise WorktreeError("Task worktree contains tracked, untracked or ignored data; cleanup refused to preserve recoverable work.")

        self._run_git(["worktree", "remove", str(root)], cwd=self.repo_root)
        dgm_logger.info(f"WorktreeManager: Removed clean task worktree {root}")
        return True
