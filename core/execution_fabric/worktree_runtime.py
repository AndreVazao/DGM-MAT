import subprocess  # nosec
import os
from pathlib import Path
from core.observability.logger import dgm_logger
from core.execution.git_utils import run_git_command, branch_exists

class WorktreeRuntime:
    """
    Manages isolated git worktrees for autonomous execution.
    """
    def __init__(self, base_path: str = ".runtime/worktrees"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def create_sandbox(self, task_id: str) -> Path:
        branch_name = f"exec-{task_id}"
        worktree_path = self.base_path / task_id

        dgm_logger.info(f"WorktreeRuntime: Creating sandbox for {task_id} at {worktree_path}")

        try:
            # git worktree add -b <branch> <path>
            args = ["worktree", "add", "-b", branch_name, str(worktree_path)]
            # If branch already exists, we might need a different approach or just use it
            if branch_exists(branch_name):
                 dgm_logger.warning(f"Branch {branch_name} already exists, attempting to use it for worktree.")
                 args = ["worktree", "add", str(worktree_path), branch_name]

            run_git_command(args, timeout=120)
            return worktree_path
        except Exception as e:
            dgm_logger.error(f"Failed to create worktree for {task_id}: {e}")
            raise

    def cleanup_sandbox(self, task_id: str):
        worktree_path = self.base_path / task_id
        dgm_logger.info(f"WorktreeRuntime: Cleaning up sandbox for {task_id}")

        if worktree_path.exists():
            run_git_command(["worktree", "remove", "--force", str(worktree_path)])
            # Delete branch
            run_git_command(["branch", "-D", f"exec-{task_id}"])
