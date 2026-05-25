import subprocess  # nosec
import os
from pathlib import Path
from core.execution.git_utils import run_git_command, branch_exists
from core.observability.logger import dgm_logger

class WorktreeManager:
    """
    Manages git worktrees for isolated agent execution.
    """
    def __init__(self, base_path: str = ".runtime/worktrees"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def create_worktree(self, branch: str, task_id: str) -> Path:
        worktree_path = self.base_path / task_id

        args = ["worktree", "add", "-b", branch, str(worktree_path)]
        if branch_exists(branch):
            dgm_logger.warning(f"Branch {branch} already exists, attempting to use it for worktree.")
            args = ["worktree", "add", str(worktree_path), branch]

        run_git_command(args)
        return worktree_path

    def cleanup_worktree(self, task_id: str):
        worktree_path = self.base_path / task_id
        if worktree_path.exists():
            run_git_command(["worktree", "remove", str(worktree_path)])
