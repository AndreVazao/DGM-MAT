import hashlib
from typing import Optional
from core.autonomy.models import AutonomousTask

class TaskGenerator:
    """Generates tasks with unique identity tracking."""
    def generate_task_id(self, title: str, repo: Optional[str] = None) -> str:
        # Use SHA256 for task hashing - Phase 39 Hardening
        content = f"{title}_{repo or 'global'}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def create_task(self, title: str, description: str, priority: int, origin: str, repo: Optional[str] = None) -> AutonomousTask:
        """Helper for tests and runtime to create task objects."""
        task_id = self.generate_task_id(title, repo)
        return AutonomousTask(
            task_id=task_id,
            title=title,
            description=description,
            priority=priority,
            assigned_agent="unassigned",
            status="PENDING",
            origin=origin,
            repo=repo
        )
