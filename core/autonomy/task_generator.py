import os
import uuid
import json
from typing import List, Dict, Any, Optional
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

    def generate_id(self) -> str:
        return str(uuid.uuid4())[:8]

    def create_task(self,
                    title: str,
                    description: str,
                    priority: int,
                    origin: str,
                    repo: Optional[str] = None,
                    risk: str = "LOW",
                    execution_type: str = "SAFE",
                    task_category: str = "tactical",
                    metadata: Dict[str, Any] = None) -> AutonomousTask:

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
        # Extend metadata with task category for reasoning
        task.metadata["category"] = task_category

        self.persist_task(task)
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

    def create_strategic_task(self, title: str, description: str, repo: str) -> AutonomousTask:
        """Creates a high-level strategic improvement task."""
        return self.create_task(
            title=f"STRATEGIC: {title}",
            description=description,
            priority=85,
            origin="strategic_planner",
            repo=repo,
            risk="MEDIUM",
            execution_type="EXPERIMENTAL",
            task_category="strategic",
            metadata={"strategic_impact": 0.9}
        )

    def scan_todos(self, repo_path: str) -> List[AutonomousTask]:
        """Scans a repository for TODO and FIXME comments."""
        tasks = []
        repo_name = os.path.basename(repo_path)
        dgm_logger.info(f"TaskGenerator: Scanning {repo_name} for TODOs...")

        for root, _, files in os.walk(repo_path):
            if ".git" in root or "__pycache__" in root:
                continue
            for file in files:
                if file.endswith((".py", ".js", ".ts", ".md")):
                    path = os.path.join(root, file)
                    try:
                        with open(path, "r", errors="ignore") as f:
                            for i, line in enumerate(f, 1):
                                if "TODO:" in line or "FIXME:" in line:
                                    clean_line = line.strip().split("TODO:")[-1].split("FIXME:")[-1].strip()
                                    tasks.append(self.create_task(
                                        title=f"Resolve TODO in {file}",
                                        description=f"Located in {path} at line {i}: {clean_line}",
                                        priority=30,
                                        origin="todo_scanner",
                                        repo=repo_name,
                                        task_category="tactical",
                                        metadata={"file": path, "line": i}
                                    ))
                    except Exception as e:
                        dgm_logger.error(f"TaskGenerator: Failed to read {path}: {e}")
        return tasks

    def ingest_failure(self, failure_report: Dict[str, Any]) -> AutonomousTask:
        """Creates a recovery task from a failed execution."""
        return self.create_task(
            title=f"Recover from failure: {failure_report.get('task_id', 'unknown')}",
            description=failure_report.get("error", "Unknown error occurred during execution."),
            priority=80,
            origin="failed_execution",
            repo=failure_report.get("repo"),
            risk="MEDIUM",
            execution_type="SYSTEM",
            task_category="maintenance",
            metadata=failure_report
        )
