from dataclasses import dataclass
from pathlib import Path

@dataclass
class ExecutionContext:
    agent_name: str
    task_id: str
    worktree_path: Path
    branch: str
    status: str = "initialized"
