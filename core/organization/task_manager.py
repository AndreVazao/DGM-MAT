"""Task lifecycle and ownership rules for the DGM-MAT organization."""

from __future__ import annotations

from threading import RLock

from .models import Task, TaskStatus, utc_now


class OrganizationTaskManager:
    """Governed task registry.

    This does not execute tasks. It establishes ownership, dependencies and
    lifecycle state so the orchestrator can safely delegate work to workers.
    """

    TERMINAL = {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED}

    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}
        self._lock = RLock()

    def create(self, task: Task) -> Task:
        with self._lock:
            if task.task_id in self._tasks:
                raise ValueError(f"Task already exists: {task.task_id}")
            self._tasks[task.task_id] = task
            return task

    def get(self, task_id: str) -> Task | None:
        with self._lock:
            return self._tasks.get(task_id)

    def dependencies_satisfied(self, task_id: str) -> bool:
        with self._lock:
            task = self._tasks[task_id]
            return all(
                self._tasks.get(dep_id) is not None
                and self._tasks[dep_id].status == TaskStatus.COMPLETED
                for dep_id in task.dependencies
            )

    def assign(self, task_id: str, agent_id: str) -> Task:
        with self._lock:
            task = self._tasks[task_id]
            if task.status not in {TaskStatus.CREATED, TaskStatus.QUEUED}:
                raise ValueError(f"Task {task_id} cannot be assigned from {task.status}.")
            if not self.dependencies_satisfied(task_id):
                raise ValueError(f"Task {task_id} has unsatisfied dependencies.")
            task.assigned_agent = agent_id
            task.status = TaskStatus.ASSIGNED
            task.updated_at = utc_now()
            return task

    def transition(self, task_id: str, status: TaskStatus) -> Task:
        with self._lock:
            task = self._tasks[task_id]
            if task.status in self.TERMINAL:
                raise ValueError(f"Task {task_id} is already terminal.")
            task.status = status
            task.updated_at = utc_now()
            return task

    def ready_tasks(self) -> list[Task]:
        with self._lock:
            return [
                task
                for task in self._tasks.values()
                if task.status in {TaskStatus.CREATED, TaskStatus.QUEUED}
                and self.dependencies_satisfied(task.task_id)
            ]
