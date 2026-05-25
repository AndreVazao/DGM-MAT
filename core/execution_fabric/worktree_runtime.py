import subprocess  # nosec
import os
import shutil
import re
from pathlib import Path
from core.observability.logger import dgm_logger
from core.execution.git_utils import run_git_command, branch_exists

class WorktreeRuntime:
    """
    Hardened worktree management for autonomous execution.
    """
    def __init__(self, base_path: str = ".runtime/worktrees"):
        self.base_path = Path(base_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _sanitize_id(self, task_id: str) -> str:
        return re.sub(r'[^a-zA-Z0-9_-]', '', task_id)

    def create_sandbox(self, task_id: str) -> Path:
        safe_id = self._sanitize_id(task_id)
        branch_name = f"exec-{safe_id}"
        worktree_path = (self.base_path / safe_id).resolve()

        # Path safety check
        if not str(worktree_path).startswith(str(self.base_path)):
            raise ValueError(f"Invalid worktree path: {worktree_path}")

        dgm_logger.info(f"WorktreeRuntime: Creating sandbox for {safe_id} at {worktree_path}")

        try:
            if branch_exists(branch_name):
                 dgm_logger.warning(f"WorktreeRuntime: Branch {branch_name} exists, reusing.")
                 args = ["worktree", "add", str(worktree_path), branch_name]
            else:
                 args = ["worktree", "add", "-b", branch_name, str(worktree_path)]

            # subprocess timeout is handled by run_git_command (if implemented correctly)
            # Ensuring no shell=True is used in run_git_command.
            run_git_command(args, timeout=120)
            return worktree_path
        except Exception as e:
            dgm_logger.error(f"WorktreeRuntime: Sandbox creation failed: {e}")
            self.cleanup_sandbox(safe_id)
            raise

    def create_snapshot(self, task_id: str):
        safe_id = self._sanitize_id(task_id)
        worktree_path = (self.base_path / safe_id).resolve()
        snapshot_path = (self.base_path / f"snapshot-{safe_id}").resolve()

        if worktree_path.exists():
            dgm_logger.info(f"WorktreeRuntime: Creating snapshot for {safe_id}")
            shutil.copytree(worktree_path, snapshot_path, dirs_exist_ok=True)

    def cleanup_sandbox(self, task_id: str):
        safe_id = self._sanitize_id(task_id)
        worktree_path = (self.base_path / safe_id).resolve()
        branch_name = f"exec-{safe_id}"

        dgm_logger.info(f"WorktreeRuntime: Cleaning up sandbox {safe_id}")

        if worktree_path.exists():
            try:
                # Use --force and handle failures gracefully
                run_git_command(["worktree", "remove", "--force", str(worktree_path)], timeout=60)
            except Exception as e:
                dgm_logger.warning(f"WorktreeRuntime: Failed to remove worktree dir: {e}")
                # Manual cleanup if git fails
                if worktree_path.exists():
                    shutil.rmtree(worktree_path, ignore_errors=True)

        try:
            if branch_exists(branch_name):
                run_git_command(["branch", "-D", branch_name], timeout=30)
        except Exception as e:
            dgm_logger.warning(f"WorktreeRuntime: Failed to delete branch {branch_name}: {e}")
