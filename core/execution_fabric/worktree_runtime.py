"""Bounded Git worktree lifecycle for isolated development tasks.

This is repository isolation, not an OS security sandbox. Validation commands are
allowlisted; no shell or arbitrary command execution is exposed.
"""
from __future__ import annotations

import os
import re
import subprocess
from threading import Thread
from pathlib import Path
from typing import Sequence

from core.observability.logger import dgm_logger


_BRANCH_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_TASK_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


class WorktreeRuntime:
    """Create, validate, test and safely retain isolated Git worktrees."""

    def __init__(
        self,
        base_path: str | Path | None = None,
        *,
        repo_path: str | Path | None = None,
        command_timeout: int = 120,
        output_limit: int = 100_000,
    ) -> None:
        self.repo_path = (
            Path(repo_path).expanduser().resolve()
            if repo_path is not None
            else Path(__file__).resolve().parents[2]
        )
        configured_base = (
            Path(base_path).expanduser()
            if base_path is not None
            else Path.home() / ".dgm-mat" / "worktrees"
        )
        self.base_path = (
            configured_base if configured_base.is_absolute()
            else self.repo_path / configured_base
        ).resolve()
        self.command_timeout = max(5, min(int(command_timeout), 600))
        self.output_limit = max(1024, min(int(output_limit), 500_000))
        self.base_path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _valid_name(value: str) -> bool:
        return isinstance(value, str) and bool(_BRANCH_RE.fullmatch(value)) and value not in {".", ".."}

    def _git(self, args: Sequence[str], *, cwd: Path | None = None, timeout: int = 30) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(cwd or self.repo_path), *args],
            shell=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout,
            check=False,
        )

    def _target_for(self, branch_name: str) -> Path:
        if not self._valid_name(branch_name):
            raise ValueError("Invalid worktree branch name.")
        target = (self.base_path / branch_name).resolve()
        if target.parent != self.base_path:
            raise ValueError("Worktree path escapes the configured worktree directory.")
        return target

    def _verify_repository(self) -> None:
        result = self._git(["rev-parse", "--show-toplevel"])
        if result.returncode != 0:
            raise RuntimeError("Configured repository path is not a Git working tree.")
        actual = Path(result.stdout.strip()).resolve()
        try:
            same_repository = actual.samefile(self.repo_path)
        except OSError:
            same_repository = False
        if not same_repository:
            raise RuntimeError("Git repository root does not match the configured repository path.")

    def _verify_worktree(self, target: Path) -> bool:
        if not target.is_dir():
            return False
        top = self._git(["rev-parse", "--show-toplevel"], cwd=target)
        if top.returncode != 0:
            return False
        try:
            if not Path(top.stdout.strip()).resolve().samefile(target):
                return False
        except OSError:
            return False
        listing = self._git(["worktree", "list", "--porcelain"])
        if listing.returncode != 0:
            return False
        for line in listing.stdout.splitlines():
            if line.startswith("worktree "):
                try:
                    if Path(line[9:]).resolve().samefile(target):
                        return True
                except OSError:
                    continue
        return False

    def create_worktree(self, branch_name: str, base_ref: str = "HEAD") -> Path | None:
        try:
            self._verify_repository()
            target = self._target_for(branch_name)
            if target.exists():
                raise FileExistsError(f"Worktree target already exists: {target}")
            if not isinstance(base_ref, str) or not base_ref or base_ref.startswith("-") or any(ch.isspace() for ch in base_ref):
                raise ValueError("Invalid worktree base reference.")
            verify = self._git(["rev-parse", "--verify", "--quiet", f"{base_ref}^{{commit}}"])
            if verify.returncode != 0:
                raise ValueError("Worktree base reference does not resolve to a commit.")
            result = self._git(
                ["worktree", "add", "-b", branch_name, str(target), base_ref],
                timeout=60,
            )
            if result.returncode != 0 or not self._verify_worktree(target):
                raise RuntimeError((result.stderr or result.stdout or "Git worktree creation failed.").strip())
            dgm_logger.info(f"WorktreeRuntime: Created isolated worktree {target}")
            return target
        except Exception as exc:
            dgm_logger.error(f"WorktreeRuntime: Worktree creation refused: {exc}")
            return None

    def create_sandbox(self, task_id: str, base_ref: str = "HEAD") -> Path | None:
        if not isinstance(task_id, str) or not _TASK_RE.fullmatch(task_id):
            dgm_logger.error("WorktreeRuntime: Invalid task ID for sandbox.")
            return None
        return self.create_worktree(f"dgm-sandbox-{task_id}", base_ref=base_ref)

    def remove_worktree(self, branch_name: str) -> bool:
        """Remove only a clean registered worktree; preserve dirty work for recovery."""
        try:
            target = self._target_for(branch_name)
            if not self._verify_worktree(target):
                return False
            status = self._git(["status", "--porcelain", "--untracked-files=all"], cwd=target)
            if status.returncode != 0 or status.stdout.strip():
                dgm_logger.warning(f"WorktreeRuntime: Preserving non-clean worktree {target}")
                return False
            result = self._git(["worktree", "remove", str(target)], timeout=60)
            if result.returncode != 0:
                dgm_logger.error(f"WorktreeRuntime: Worktree removal failed: {result.stderr.strip()}")
                return False
            return True
        except Exception as exc:
            dgm_logger.error(f"WorktreeRuntime: Worktree removal refused: {exc}")
            return False

    def cleanup_sandbox(self, task_id: str) -> bool:
        if not isinstance(task_id, str) or not _TASK_RE.fullmatch(task_id):
            return False
        return self.remove_worktree(f"dgm-sandbox-{task_id}")

    def _run_bounded(
        self,
        argv: list[str],
        target: Path,
        environment: dict[str, str],
    ) -> subprocess.CompletedProcess[str]:
        process = subprocess.Popen(
            argv,
            shell=False,
            cwd=target,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout_buffer = bytearray()
        stderr_buffer = bytearray()

        def drain(stream, buffer: bytearray) -> None:
            while True:
                chunk = stream.read1(8192)
                if not chunk:
                    return
                remaining = self.output_limit - len(buffer)
                if remaining > 0:
                    buffer.extend(chunk[:remaining])

        readers = [
            Thread(target=drain, args=(process.stdout, stdout_buffer), daemon=True),
            Thread(target=drain, args=(process.stderr, stderr_buffer), daemon=True),
        ]
        for reader in readers:
            reader.start()
        timed_out = False
        try:
            process.wait(timeout=self.command_timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            process.kill()
            process.wait()
        for reader in readers:
            reader.join(timeout=5)
        if process.stdout is not None:
            process.stdout.close()
        if process.stderr is not None:
            process.stderr.close()
        stdout = bytes(stdout_buffer).decode("utf-8", errors="replace")
        stderr = bytes(stderr_buffer).decode("utf-8", errors="replace")
        if timed_out:
            stderr = (stderr + "\n[validation command timed out]")[-self.output_limit:]
        return subprocess.CompletedProcess(argv, 124 if timed_out else process.returncode, stdout, stderr)

    @staticmethod
    def _safe_test_target(target: Path, relative_path: str) -> bool:
        try:
            resolved_root = target.resolve()
            test_root = (resolved_root / "tests").resolve()
            test_root.relative_to(resolved_root)
            candidate = (resolved_root / relative_path).resolve()
            candidate.relative_to(test_root)
            return candidate.is_file() and candidate.suffix.casefold() == ".py"
        except (OSError, ValueError):
            return False

    def execute_in_worktree(
        self,
        branch_name: str,
        command: Sequence[str],
    ) -> subprocess.CompletedProcess[str] | None:
        """Run only a fixed validation command in a verified worktree."""
        try:
            target = self._target_for(branch_name)
            if not self._verify_worktree(target):
                return None
            if isinstance(command, (str, bytes)) or not isinstance(command, (list, tuple)):
                raise ValueError("Commands must be an argument list from the validation catalogue.")
            argv = list(command)
            if (
                len(argv) == 5
                and argv[:4] == ["python", "-m", "pytest", "-q"]
                and isinstance(argv[4], str)
                and argv[4].startswith("tests/")
                and not Path(argv[4]).is_absolute()
                and ".." not in Path(argv[4]).parts
                and self._safe_test_target(target, argv[4])
            ):
                pass
            else:
                raise ValueError("Command is not present in the bounded validation catalogue.")
            environment = os.environ.copy()
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            execution_argv = ["python", "-m", "pytest", "-q", "-p", "no:cacheprovider", argv[4]]
            return self._run_bounded(execution_argv, target, environment)
        except Exception as exc:
            dgm_logger.error(f"WorktreeRuntime: Validation command refused or failed: {exc}")
            return None
