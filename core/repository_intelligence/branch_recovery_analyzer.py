"""Read-only Git branch archaeology and recovery recommendations.

This analyzer never fetches, checks out, commits, creates refs, rebases, merges,
cherry-picks, deletes, or modifies a working tree. It only inspects objects
already present in a local repository.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Callable, Any


_SHA = re.compile(r"^[0-9a-f]{40,64}$")


class BranchRecoveryAuditError(ValueError):
    pass


class BranchRecoveryAnalyzer:
    def __init__(
        self,
        command_runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
        timeout: int = 15,
    ) -> None:
        self.command_runner = command_runner or subprocess.run
        self.timeout = timeout

    def audit_repository(self, repository_path: str | Path, default_branch: str) -> dict[str, Any]:
        root = Path(repository_path).resolve()
        if not root.is_dir() or not (root / ".git").exists():
            raise BranchRecoveryAuditError("repository_path_must_be_a_git_worktree")
        if not self._valid_ref(default_branch):
            raise BranchRecoveryAuditError("default_branch_invalid")

        default_ref = f"refs/heads/{default_branch}"
        default_sha = self._git(root, "rev-parse", "--verify", default_ref)
        if not default_sha or not _SHA.fullmatch(default_sha):
            raise BranchRecoveryAuditError("default_branch_not_available_locally")

        status = self._git(root, "status", "--porcelain=v1", "--untracked-files=all")
        dirty_paths = self._parse_status_paths(status)
        refs = self._git(root, "for-each-ref", "--format=%(refname:short)|%(objectname)", "refs/heads")
        branches = []
        for line in refs.splitlines():
            name, sep, sha = line.partition("|")
            if not sep or not self._valid_ref(name) or not _SHA.fullmatch(sha):
                continue
            if name == default_branch:
                continue
            branches.append(self._inspect_branch(root, default_branch, default_sha, name, sha))

        branches.sort(key=lambda item: (item["recommendation"], item["branch"].casefold()))
        return {
            "schema": "dgm-mat.branch-recovery-audit.v1",
            "repository": str(root),
            "default_branch": default_branch,
            "default_sha": default_sha,
            "working_tree_dirty": bool(dirty_paths),
            "working_tree_paths": dirty_paths,
            "branch_count": len(branches),
            "branches": branches,
            "read_only": True,
            "mutations_performed": [],
            "safety_note": "Local object database only. Remote-only refs and uncommitted file contents are not copied or changed.",
        }

    def compare_remote_branch(
        self,
        repository_path: str | Path,
        *,
        local_branch: str,
        remote_sha: str,
    ) -> dict[str, Any]:
        """Compare a GitHub SHA only if its object is already present locally."""
        root = Path(repository_path).resolve()
        if not self._valid_ref(local_branch) or not _SHA.fullmatch(remote_sha or ""):
            raise BranchRecoveryAuditError("remote_branch_comparison_input_invalid")
        local_sha = self._git(root, "rev-parse", "--verify", f"refs/heads/{local_branch}")
        if not local_sha:
            return {"status": "LOCAL_BRANCH_MISSING", "local_branch": local_branch, "remote_sha": remote_sha}
        object_type = self._git(root, "cat-file", "-t", remote_sha)
        if object_type != "commit":
            return {
                "status": "REMOTE_OBJECT_NOT_LOCAL",
                "local_branch": local_branch,
                "local_sha": local_sha,
                "remote_sha": remote_sha,
                "ahead": None,
                "behind": None,
                "changed_files": [],
            }
        return self._compare_refs(root, local_branch, local_sha, remote_sha)

    def _inspect_branch(self, root: Path, default_branch: str, default_sha: str, branch: str, sha: str) -> dict[str, Any]:
        counts = self._git(root, "rev-list", "--left-right", "--count", f"{default_sha}...{sha}")
        try:
            behind, ahead = [int(value) for value in counts.split()]
        except (ValueError, TypeError):
            behind = ahead = None
        if ahead is None or behind is None:
            status = "NOT_COMPARABLE"
            files: list[dict[str, str]] = []
            commits: list[str] = []
        else:
            status = "SYNCED" if ahead == 0 and behind == 0 else (
                "AHEAD" if ahead > 0 and behind == 0 else
                "BEHIND" if ahead == 0 and behind > 0 else "DIVERGED"
            )
            files = self._changed_files(root, f"{default_sha}...{sha}") if ahead else []
            commits = self._commit_subjects(root, f"{default_sha}..{sha}") if ahead else []

        integrated = self._git(root, "merge-base", "--is-ancestor", sha, default_sha, return_code=True) == "0"
        if integrated:
            recommendation = "ALREADY_INTEGRATED_REVIEW_FOR_ARCHIVE"
        elif status == "BEHIND":
            recommendation = "NO_UNIQUE_COMMITS_REVIEW_BEFORE_ARCHIVE"
        elif status == "AHEAD":
            recommendation = "PRESERVE_AND_REVIEW_UNIQUE_WORK"
        elif status == "DIVERGED":
            recommendation = "PRESERVE_AND_RECONCILE_FILE_BY_FILE"
        else:
            recommendation = "INSUFFICIENT_LOCAL_EVIDENCE"

        return {
            "branch": branch,
            "sha": sha,
            "default_branch": default_branch,
            "status": status,
            "ahead_commits": ahead,
            "behind_commits": behind,
            "already_integrated": integrated,
            "unique_commit_subjects": commits[:100],
            "unique_commit_subjects_truncated": len(commits) > 100,
            "changed_files_vs_default": files[:500],
            "changed_files_truncated": len(files) > 500,
            "recommendation": recommendation,
            "automatic_action": "NONE",
        }

    def _compare_refs(self, root: Path, label: str, local_sha: str, remote_sha: str) -> dict[str, Any]:
        counts = self._git(root, "rev-list", "--left-right", "--count", f"{local_sha}...{remote_sha}")
        try:
            ahead, behind = [int(value) for value in counts.split()]
        except (ValueError, TypeError):
            return {"status": "NOT_COMPARABLE", "local_branch": label, "local_sha": local_sha, "remote_sha": remote_sha}
        status = "SYNCED" if ahead == 0 and behind == 0 else (
            "REMOTE_AHEAD" if ahead == 0 else "LOCAL_AHEAD" if behind == 0 else "DIVERGED"
        )
        files = self._changed_files(root, f"{local_sha}...{remote_sha}") if ahead else []
        return {
            "status": status,
            "local_branch": label,
            "local_sha": local_sha,
            "remote_sha": remote_sha,
            "ahead": ahead,
            "behind": behind,
            "changed_files": files[:500],
            "changed_files_truncated": len(files) > 500,
        }

    def _changed_files(self, root: Path, revision_range: str) -> list[dict[str, str]]:
        output = self._git(root, "diff", "--name-status", "--find-renames", revision_range)
        files = []
        for line in output.splitlines():
            parts = line.split("\t")
            if len(parts) >= 2:
                files.append({"status": parts[0], "path": parts[-1]})
        return files

    def _commit_subjects(self, root: Path, revision_range: str) -> list[str]:
        output = self._git(root, "log", "--format=%h %s", "--no-decorate", revision_range)
        return [line[:500] for line in output.splitlines() if line.strip()]

    def _git(self, root: Path, *args: str, return_code: bool = False) -> str:
        try:
            result = self.command_runner(
                ["git", "-c", f"safe.directory={root}", "-C", str(root), *args],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=self.timeout, check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return ""
        if return_code:
            return str(result.returncode)
        return result.stdout.strip() if result.returncode == 0 else ""

    @staticmethod
    def _valid_ref(value: str) -> bool:
        if not isinstance(value, str) or not value or value.startswith("-") or value.startswith("/") or value.endswith("/"):
            return False
        if ".." in value or "@{" in value or any(ch in value for ch in " ~^:?*[\\"):
            return False
        return all(part not in {"", ".", ".."} for part in value.split("/"))

    @staticmethod
    def _parse_status_paths(status: str) -> list[str]:
        paths = []
        for line in status.splitlines():
            if len(line) >= 4:
                path = line[3:]
                if " -> " in path:
                    path = path.split(" -> ", 1)[1]
                paths.append(path[:1000])
        return paths[:1000]
