import subprocess
import os
from pathlib import Path

class WorktreeManager:
    def __init__(self, base_path: str = "worktrees"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)

    def create_worktree(self, agent_name: str, task_id: str, branch: str):
        worktree_path = self.base_path / f"{agent_name}-{task_id}"
        cmd = ["git", "worktree", "add", "-b", branch, str(worktree_path)]
        subprocess.run(  # noseccmd, check=True)
        return worktree_path

    def remove_worktree(self, agent_name: str, task_id: str):
        worktree_path = self.base_path / f"{agent_name}-{task_id}"
        if worktree_path.exists():
            subprocess.run(  # nosec["git", "worktree", "remove", str(worktree_path)], check=True)
