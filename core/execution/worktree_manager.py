import subprocess  # nosec
import os
from pathlib import Path

class WorktreeManager:
    """
    Manages git worktrees for isolated agent execution.
    """
    def __init__(self, base_path: str = ".runtime/worktrees"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def create_worktree(self, branch: str, task_id: str) -> Path:
        worktree_path = self.base_path / task_id
        cmd = ["git", "worktree", "add", "-b", branch, str(worktree_path)]
        subprocess.run(cmd, check=True)  # nosec
        return worktree_path

    def cleanup_worktree(self, task_id: str):
        worktree_path = self.base_path / task_id
        if worktree_path.exists():
            subprocess.run(["git", "worktree", "remove", str(worktree_path)], check=True)  # nosec
