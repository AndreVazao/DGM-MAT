import hashlib
from typing import Optional

class TaskGenerator:
    """Generates tasks with unique identity tracking."""
    def generate_task_id(self, title: str, repo: Optional[str] = None) -> str:
        # Use SHA256 for task hashing - Phase 39 Hardening
        content = f"{title}_{repo or 'global'}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
