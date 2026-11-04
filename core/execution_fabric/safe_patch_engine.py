"""Apply reviewed patches only inside a registered, non-primary Git worktree."""
from __future__ import annotations

import os
from pathlib import Path, PurePosixPath
import subprocess
from typing import Any

from core.observability.logger import dgm_logger


class SafePatchEngine:
    """Generate and assess diffs; apply only to an explicitly supplied worktree."""

    def __init__(self, repository_root: str | Path | None = None, max_patch_bytes: int = 1_000_000) -> None:
        self.repository_root = (
            Path(repository_root).expanduser().resolve()
            if repository_root is not None
            else Path(__file__).resolve().parents[2]
        )
        self.max_patch_bytes = max(1024, min(int(max_patch_bytes), 5_000_000))

    def _git(self, path: Path, args: list[str], *, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(path), *args],
            input=input_text,
            shell=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
            timeout=30,
        )

    def _registered_worktree(self, worktree_path: str | Path) -> Path:
        target = Path(worktree_path).expanduser().resolve()
        if not target.is_dir():
            raise ValueError("Patch target must be an existing directory.")
        try:
            if target.samefile(self.repository_root):
                raise ValueError("Patches may never be applied to the primary repository.")
        except OSError:
            pass
        top = self._git(target, ["rev-parse", "--show-toplevel"])
        try:
            same_worktree = top.returncode == 0 and Path(top.stdout.strip()).resolve().samefile(target)
        except OSError:
            same_worktree = False
        if not same_worktree:
            raise ValueError("Patch target is not the root of a Git working tree.")
        listing = self._git(self.repository_root, ["worktree", "list", "--porcelain"])
        if listing.returncode != 0:
            raise ValueError("Unable to verify registered Git worktrees.")
        registered = False
        for line in listing.stdout.splitlines():
            if line.startswith("worktree "):
                try:
                    if Path(line[9:]).resolve().samefile(target):
                        registered = True
                        break
                except OSError:
                    continue
        if not registered:
            raise ValueError("Patch target is not registered as a worktree of the primary repository.")
        return target

    @staticmethod
    def _validate_patch_paths(patch: str) -> None:
        for line in patch.splitlines():
            if not (line.startswith("+++ ") or line.startswith("--- ")):
                continue
            raw = line[4:].split("\t", 1)[0].strip()
            if raw == "/dev/null":
                continue
            if raw.startswith(("a/", "b/")):
                raw = raw[2:]
            path = PurePosixPath(raw)
            if path.is_absolute() or ".." in path.parts or ":" in raw or "\\" in raw:
                raise ValueError("Patch contains an absolute or escaping file path.")

    def generate_patch(self, worktree_path: Path) -> str:
        target = self._registered_worktree(worktree_path)
        untracked = self._git(target, ["ls-files", "--others", "--exclude-standard"])
        if untracked.returncode != 0:
            raise RuntimeError((untracked.stderr or "Unable to inspect untracked worktree files.").strip())
        if untracked.stdout.strip():
            raise ValueError(
                "Untracked files are not silently omitted from a development patch; "
                "preserve the worktree and review the new files explicitly."
            )
        result = self._git(target, ["diff", "--no-ext-diff", "HEAD", "--"])
        if result.returncode != 0:
            raise RuntimeError((result.stderr or "Unable to generate worktree diff.").strip())
        if len(result.stdout.encode("utf-8")) > self.max_patch_bytes:
            raise ValueError("Generated patch exceeds the configured size limit.")
        return result.stdout

    def assess_risk(self, patch: str) -> dict[str, Any]:
        lines = patch.splitlines()
        score = 0.0
        warnings: list[str] = []
        blocked = False
        if len(lines) > 200:
            score += 0.3
            warnings.append("Large patch detected")
        blocked_patterns = (
            "os.system", "subprocess.popen(shell=true)", "subprocess.run(shell=true)",
            "rm -rf", "format ", "drop table", "delete from", "registry.delete",
            "shutil.rmtree", "os.remove", ".unlink()",
        )
        credential_patterns = (".env", "secrets", "password", "api_key", "token", "access_key")
        for line in lines:
            if line.startswith("+"):
                lowered = line.lower()
                if any(pattern in lowered for pattern in blocked_patterns):
                    blocked = True
                    score = 1.0
                    warnings.append("Destructive operation pattern detected in added line.")
                if any(pattern in lowered for pattern in credential_patterns):
                    score = max(score, 0.8)
                    warnings.append("Credential-like pattern detected in added line.")
        level = "CRITICAL" if blocked else "HIGH" if score > 0.7 else "MEDIUM" if score > 0.4 else "LOW"
        return {"score": min(score, 1.0), "level": level, "warnings": warnings, "is_blocked": blocked}

    def apply_patch(self, patch: str, worktree_path: str | Path) -> None:
        """Check and apply a patch inside a registered non-primary worktree only."""
        if not isinstance(patch, str) or not patch.strip():
            raise ValueError("Patch must be a non-empty string.")
        if len(patch.encode("utf-8")) > self.max_patch_bytes:
            raise ValueError("Patch exceeds the configured size limit.")
        self._validate_patch_paths(patch)
        risk = self.assess_risk(patch)
        if risk["is_blocked"]:
            raise SecurityError("Destructive patch execution blocked.")
        target = self._registered_worktree(worktree_path)
        check = self._git(target, ["apply", "--check", "-"], input_text=patch)
        if check.returncode != 0:
            raise ValueError((check.stderr or "Patch does not apply cleanly to the target worktree.").strip())
        result = self._git(target, ["apply", "-"], input_text=patch)
        if result.returncode != 0:
            raise RuntimeError((result.stderr or "Patch application failed.").strip())
        dgm_logger.info(f"SafePatchEngine: Applied patch inside isolated worktree {target}")


class SecurityError(Exception):
    pass
