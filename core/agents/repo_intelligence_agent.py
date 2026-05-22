from typing import Any
from core.agents.base import BaseAgent
from core.event_bus.bus import Event, EventBus
import os

class RepoIntelligenceAgent(BaseAgent):
    def __init__(self, agent_id: str, event_bus: EventBus):
        super().__init__(agent_id, "repo_intel", event_bus)

    def execute_logic(self, task: Event) -> Any:
        task_type = task.payload.get("task_type")
        if task_type == "analyze_structure":
            return self._analyze_structure()
        return f"Repo Intel processed {task_type}"

    def _analyze_structure(self):
        # Real logic for Task 3
        structure = []
        for root, dirs, files in os.walk("."):
            if ".git" in dirs: dirs.remove(".git")
            level = root.replace(".", "").count(os.sep)
            indent = " " * 4 * level
            structure.append(f"{indent}{os.path.basename(root)}/")
        return "\n".join(structure[:20]) # Limit output for demo
