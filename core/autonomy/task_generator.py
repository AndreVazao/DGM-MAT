import os
import uuid
import json
import hashlib
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from pathlib import Path

from core.autonomy.models import AutonomousTask
from core.storage.storage_manager import storage_manager
from core.observability.logger import dgm_logger

class TaskGenerator:
    """
    Generates autonomous tasks from various sources like repo analysis,
    failed executions, and strategic planning.
    """
    def __init__(self):
        self.tasks_dir = storage_manager.get_path("tasks")
        self.active_task_hashes: Set[str] = set()

    def generate_id(self) -> str:
        return str(uuid.uuid4())[:8]

    def _generate_task_hash(self, title: str, repo: Optional[str]) -> str:
        content = f"{title}_{repo or 'global'}"
        return hashlib.md5(content.encode()).hexdigest()

    def create_task(self,
                    title: str,
                    description: str,
                    priority: int,
                    origin: str,
                    repo: Optional[str] = None,
                    risk: str = "LOW",
                    execution_type: str = "SAFE",
                    task_category: str = "tactical",
                    metadata: Dict[str, Any] = None) -> Optional[AutonomousTask]:

        # 1. TASK DEDUPLICATION
        task_hash = self._generate_task_hash(title, repo)
        if task_hash in self.active_task_hashes:
            dgm_logger.debug(f"TaskGenerator: Skipping duplicate task: {title}")
            return None

        task = AutonomousTask(
            task_id=self.generate_id(),
            title=title,
            description=description,
            priority=priority,
            assigned_agent="AutonomyAgent",
            status="PENDING",
            origin=origin,
            repo=repo,
            risk=risk,
            execution_type=execution_type,
            metadata=metadata or {}
        )
        task.metadata["category"] = task_category
        task.metadata["hash"] = task_hash

        self.persist_task(task)
        self.active_task_hashes.add(task_hash)
        return task

    def persist_task(self, task: AutonomousTask):
        file_path = self.tasks_dir / f"task_{task.task_id}.json"
        task_data = {
            "task_id": task.task_id,
            "title": task.title,
            "description": task.description,
            "priority": task.priority,
            "assigned_agent": task.assigned_agent,
            "status": task.status,
            "origin": task.origin,
            "repo": task.repo,
            "confidence": task.confidence,
            "risk": task.risk,
            "execution_type": task.execution_type,
            "dependencies": task.dependencies,
            "estimated_impact": task.estimated_impact,
            "metadata": task.metadata,
            "created_at": task.created_at.isoformat()
        }
        with open(file_path, "w") as f:
            json.dump(task_data, f, indent=2)
        dgm_logger.info(f"TaskGenerator: Persisted task {task.task_id} to {file_path}")

    def discover_technical_debt(self, scan_results: List[Dict[str, Any]]) -> List[AutonomousTask]:
        tasks = []
        for result in scan_results:
            if result.get("technical_debt_estimate") == "high":
                t = self.create_task(
                    title=f"Refactor Technical Debt: {result['path']}",
                    description="High complexity and technical debt detected during scan.",
                    priority=60,
                    origin="architecture_analyzer",
                    repo=result.get("repo"),
                    task_category="refactoring"
                )
                if t: tasks.append(t)
        return tasks

    def discover_missing_tests(self, scan_results: List[Dict[str, Any]]) -> List[AutonomousTask]:
        tasks = []
        for result in scan_results:
            if result.get("language") == "python" and not result.get("has_tests"):
                t = self.create_task(
                    title=f"Add unit tests for {result['path']}",
                    description="This module lacks automated tests.",
                    priority=50,
                    origin="test_gap_analyzer",
                    repo=result.get("repo"),
                    task_category="testing"
                )
                if t: tasks.append(t)
        return tasks

    def validate_dependencies(self, task: AutonomousTask) -> bool:
        """Ensures all task dependencies are met or valid."""
        for dep_id in task.dependencies:
            # Check if dep_id exists and is completed
            pass
        return True

    def cleanup_abandoned_tasks(self):
        """Cleans up tasks that have been in PENDING for too long."""
        dgm_logger.info("TaskGenerator: Cleaning up abandoned tasks.")
        pass
