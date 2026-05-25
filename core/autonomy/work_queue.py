import json
import time
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from core.storage.storage_manager import storage_manager
from core.observability.logger import dgm_logger

class WorkTask:
    def __init__(self, id: str, type: str, payload: Dict[str, Any], priority: int = 10, status: str = "pending", created_at: float = None, retry_count: int = 0, locked_until: float = 0):
        self.id = id
        self.type = type
        self.payload = payload
        self.priority = priority
        self.status = status
        self.created_at = created_at or time.time()
        self.retry_count = retry_count
        self.locked_until = locked_until

    def to_dict(self):
        return self.__dict__

class WorkQueue:
    """
    Persistent, priority-based autonomous work queue.
    """
    def __init__(self):
        self.storage_path = storage_manager.get_path("tasks")
        self.tasks: List[WorkTask] = []
        self._load_tasks()

    def _load_tasks(self):
        """Loads tasks from persistent storage."""
        if not self.storage_path.exists():
            self.storage_path.mkdir(parents=True, exist_ok=True)
            return

        for task_file in self.storage_path.glob("*.json"):
            try:
                data = json.loads(task_file.read_text())
                task = WorkTask(**data)
                self.tasks.append(task)
            except Exception as e:
                dgm_logger.error(f"WorkQueue: Failed to load task {task_file}: {e}")

    def add_task(self, task_type: str, payload: Dict[str, Any], priority: int = 10) -> str:
        task_id = f"task_{int(time.time())}_{os.urandom(4).hex()}"
        task = WorkTask(id=task_id, type=task_type, payload=payload, priority=priority)
        self.tasks.append(task)
        self._persist_task(task)
        dgm_logger.info(f"WorkQueue: Added task {task_id} ({task_type})")
        return task_id

    def lease_task(self) -> Optional[WorkTask]:
        """Leases the highest priority pending task."""
        pending = [t for t in self.tasks if t.status == "pending" and t.locked_until < time.time()]
        if not pending:
            return None

        pending.sort(key=lambda x: (-x.priority, x.created_at))
        task = pending[0]
        task.status = "running"
        task.locked_until = time.time() + 300
        self._persist_task(task)
        return task

    def complete_task(self, task_id: str):
        for task in self.tasks:
            if task.id == task_id:
                task.status = "completed"
                self._persist_task(task)
                dgm_logger.info(f"WorkQueue: Completed task {task_id}")
                return

    def fail_task(self, task_id: str, retry: bool = True):
        for task in self.tasks:
            if task.id == task_id:
                task.status = "failed"
                if retry and task.retry_count < 3:
                    task.status = "pending"
                    task.retry_count += 1
                    task.locked_until = time.time() + (60 * task.retry_count)
                self._persist_task(task)
                dgm_logger.warning(f"WorkQueue: Task {task_id} failed. Retry: {retry}")
                return

    def _persist_task(self, task: WorkTask):
        file_path = self.storage_path / f"{task.id}.json"
        try:
            file_path.write_text(json.dumps(task.to_dict(), indent=2))
        except Exception as e:
            dgm_logger.error(f"WorkQueue: Failed to persist task {task.id}: {e}")

    def health(self) -> Dict[str, Any]:
        return {
            "queue_size": len(self.tasks),
            "pending": len([t for t in self.tasks if t.status == "pending"]),
            "running": len([t for t in self.tasks if t.status == "running"]),
            "completed": len([t for t in self.tasks if t.status == "completed"]),
            "failed": len([t for t in self.tasks if t.status == "failed"])
        }

    def metrics(self) -> Dict[str, Any]:
        return {
            "total_tasks": len(self.tasks)
        }
