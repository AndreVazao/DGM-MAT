from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from core.observability.logger import dgm_logger


class SecurityError(RuntimeError):
    """Raised when a patch would cross the isolated-worktree boundary."""


class SafePatchEngine:
    """
    Generate, assess and apply patches without ever writing to the primary checkout.

    Applying a patch requires two explicit repository roots:
    - expected_repo_root: the primary repository checkout;
    - worktree_path: a separate Git worktree belonging to that repository.

    The target worktree must be clean and on a non-protected branch. Git is always
    invoked with an explicit -C path, shell execution is never used, and redirects
    or unsafe-path flags are not involved.
    """

    MAX_PATCH_BYTES = 512_000
    GIT_TIMEOUT_SECONDS = 20
    PROTECTED_BRANCHES = frozenset({"main", "master", "develop", "release", "production", "stable", "trunk"})
    PROTECTED_BRANCH_PREFIXES = ("release/", "production/", "stable/")

    @staticmethod
    def _run_git(repo_path: Path, args: list[str]) -> str:
        try:
            result = subprocess.run(
                ["git", "-C", str(repo_path), *args],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                shell=False,
                timeout=SafePatchEngine.GIT_TIMEOUT_SECONDS,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise SecurityError(f"Git validation failed: {type(exc).__name__}") from None
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "Git command failed").strip()
            raise SecurityError(detail[:240])
        # Preserve leading spaces: porcelain status uses them as state columns.
        return result.stdout.rstrip()

    @classmethod
    def _repo_root(cls, path: str | Path, label: str) -> Path:
        try:
            resolved = Path(path).expanduser().resolve(strict=True)
        except (OSError, RuntimeError, TypeError) as exc:
            raise SecurityError(f"{label} does not resolve: {type(exc).__name__}") from None
        if not resolved.is_dir():
            raise SecurityError(f"{label} must be an existing directory.")
        reported_root = cls._run_git(resolved, ["rev-parse", "--show-toplevel"])
        try:
            root = Path(reported_root).resolve(strict=True)
        except (OSError, RuntimeError):
            raise SecurityError(f"{label} is not a valid Git working tree.") from None
        if root != resolved:
            raise SecurityError(f"{label} must be the exact Git worktree root.")
        return root

    @classmethod
    def _git_common_dir(cls, repo_root: Path) -> Path:
        raw = cls._run_git(repo_root, ["rev-parse", "--git-common-dir"])
        common = Path(raw)
        if not common.is_absolute():
            common = repo_root / common
        try:
            return common.resolve(strict=True)
        except (OSError, RuntimeError):
            raise SecurityError("Git common directory cannot be resolved.") from None

    @classmethod
    def _branch_name(cls, repo_root: Path) -> str:
        branch = cls._run_git(repo_root, ["branch", "--show-current"]).strip()
        if not branch:
            raise SecurityError("Detached HEAD worktrees cannot receive autonomous patches.")
        normalized = branch.casefold()
        if normalized in cls.PROTECTED_BRANCHES or normalized.startswith(cls.PROTECTED_BRANCH_PREFIXES):
            raise SecurityError(f"Protected branch '{branch}' cannot receive autonomous patches.")
        return branch

    def generate_patch(self, worktree_path: Path) -> str:
        """Return the unstaged binary-capable diff from an exact worktree root."""
        try:
            root = self._repo_root(worktree_path, "Patch source")
            result = subprocess.run(
                [
                    "git", "-C", str(root), "diff",
                    "--binary", "--no-ext-diff", "--no-textconv",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=True,
                shell=False,
                timeout=self.GIT_TIMEOUT_SECONDS,
            )
            if len(result.stdout.encode("utf-8")) > self.MAX_PATCH_BYTES:
                raise SecurityError("Generated patch exceeds the 512 KB safety limit.")
            return result.stdout
        except subprocess.CalledProcessError as exc:
            dgm_logger.error(f"SafePatchEngine: git diff failed with exit code {exc.returncode}")
            return ""
        except (OSError, subprocess.TimeoutExpired, SecurityError) as exc:
            dgm_logger.error(f"SafePatchEngine: patch generation refused: {type(exc).__name__}")
            return ""

    def assess_risk(self, patch: str) -> dict[str, Any]:
        """Heuristic review aid; this is not a substitute for the isolation boundary."""
        lines = patch.splitlines()
        score = 0.0
        warnings: list[str] = []
        is_blocked = False

        if len(lines) > 200:
            score += 0.3
            warnings.append("Large patch detected")

        blocked_patterns = (
            "os.system",
            "subprocess.popen(shell=true)",
            "subprocess.run(shell=true)",
            "rm -rf",
            "format ",
            "drop table",
            "delete from",
            "registry.delete",
            "shutil.rmtree",
            "os.remove",
            ".unlink()",
        )
        credential_patterns = (".env", "secrets", "password", "api_key", "token", "access_key")

        for line in lines:
            if not line.startswith("+") or line.startswith("+++"):
                continue
            lower_line = line.lower()
            if any(pattern in lower_line for pattern in blocked_patterns):
                score = 1.0
                is_blocked = True
                warnings.append("SECURITY BLOCK: destructive operation pattern detected")
            if any(pattern in lower_line for pattern in credential_patterns):
                score = max(score, 0.8)
                warnings.append("SECURITY WARNING: credential-like pattern detected")

        if is_blocked:
            risk_level = "CRITICAL"
        elif score > 0.7:
            risk_level = "HIGH"
        elif score > 0.4:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return {
            "score": min(score, 1.0),
            "level": risk_level,
            "warnings": warnings,
            "is_blocked": is_blocked,
        }

    def apply_patch(
        self,
        patch: str,
        worktree_path: str | Path | None = None,
        expected_repo_root: str | Path | None = None,
    ) -> dict[str, Any]:
        """
        Apply only to a clean, non-protected worktree of the expected repository.

        The legacy one-argument call is deliberately rejected. This method never
        infers a destination from the current working directory.
        """
        if not isinstance(patch, str) or not patch.strip():
            raise SecurityError("An explicit, non-empty unified diff is required.")
        if len(patch.encode("utf-8")) > self.MAX_PATCH_BYTES:
            raise SecurityError("Patch exceeds the 512 KB safety limit.")
        if "\x00" in patch:
            raise SecurityError("Binary NUL content is not accepted in textual patches.")
        if worktree_path is None or expected_repo_root is None:
            raise SecurityError("Applying patches requires an explicit isolated worktree and expected repository root.")

        risk = self.assess_risk(patch)
        if risk["is_blocked"]:
            dgm_logger.error("SafePatchEngine: destructive patch pattern rejected.")
            raise SecurityError("Destructive patch pattern detected.")

        target_root = self._repo_root(worktree_path, "Patch destination")
        primary_root = self._repo_root(expected_repo_root, "Expected primary repository")
        if target_root == primary_root:
            raise SecurityError("The primary repository checkout is never a patch destination.")

        target_common = self._git_common_dir(target_root)
        primary_common = self._git_common_dir(primary_root)
        if target_common != primary_common:
            raise SecurityError("Patch destination is not a worktree of the expected repository.")

        branch = self._branch_name(target_root)
        status = self._run_git(target_root, ["status", "--porcelain", "--untracked-files=all"])
        if status:
            raise SecurityError("Patch destination must be clean before patch application.")

        check = subprocess.run(
            ["git", "-C", str(target_root), "apply", "--check", "--whitespace=error"],
            input=patch,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            shell=False,
            timeout=self.GIT_TIMEOUT_SECONDS,
        )
        if check.returncode != 0:
            detail = (check.stderr or check.stdout or "Patch validation failed").strip()
            raise SecurityError(f"Patch validation failed: {detail[:200]}")

        applied = subprocess.run(
            ["git", "-C", str(target_root), "apply", "--whitespace=error"],
            input=patch,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            shell=False,
            timeout=self.GIT_TIMEOUT_SECONDS,
        )
        if applied.returncode != 0:
            detail = (applied.stderr or applied.stdout or "Patch application failed").strip()
            raise SecurityError(f"Patch application failed: {detail[:200]}")

        changed = self._run_git(target_root, ["status", "--porcelain", "--untracked-files=all"])
        if not changed:
            raise SecurityError("Git reported success but no worktree changes were observed.")

        changed_files = [
            line[3:].strip()
            for line in changed.splitlines()
            if len(line) >= 4
        ]
        dgm_logger.info(
            f"SafePatchEngine: applied patch to isolated branch {branch}; "
            f"{len(changed_files)} changed path(s); primary checkout untouched."
        )
        return {
            "applied": True,
            "branch": branch,
            "worktree_path": str(target_root),
            "changed_files": changed_files,
            "risk": risk,
        }
