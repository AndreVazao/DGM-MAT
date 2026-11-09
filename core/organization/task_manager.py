"""Governed task lifecycle with optional restart-safe SQLite persistence."""
from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime
from threading import RLock
from typing import TYPE_CHECKING, Any

from .models import Evidence, Task, TaskStatus, utc_now

if TYPE_CHECKING:
    from .message_bus import InternalMessageBus


class OrganizationTaskManager:
    """Task registry; execution remains the responsibility of worker runtimes.

    Passing the existing InternalMessageBus enables durable storage in its
    SQLite database. Omitting it deliberately preserves the lightweight,
    process-local mode used by isolated callers and tests.
    """

    TERMINAL = {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED}
    SCHEMA_VERSION = 1

    def __init__(self, message_bus: InternalMessageBus | None = None) -> None:
        self._tasks: dict[str, Task] = {}
        self._revisions: dict[str, int] = {}
        self._message_bus = message_bus
        self._lock = RLock()
        if message_bus is not None:
            self._restore()

    @staticmethod
    def _datetime(value: Any, field_name: str) -> datetime:
        if not isinstance(value, str):
            raise ValueError(f"{field_name} must be an ISO-8601 string")
        try:
            return datetime.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(f"Invalid {field_name}: {value!r}") from exc

    @classmethod
    def _serialize(cls, task: Task) -> dict[str, Any]:
        payload = asdict(task)
        payload["status"] = task.status.value
        payload["created_at"] = task.created_at.isoformat()
        payload["updated_at"] = task.updated_at.isoformat()
        payload["evidence"] = [
            {
                **asdict(item),
                "captured_at": item.captured_at.isoformat(),
            }
            for item in task.evidence
        ]
        return payload

    @classmethod
    def _deserialize(cls, payload_json: str, expected_task_id: str) -> Task:
        try:
            payload = json.loads(payload_json)
            if not isinstance(payload, dict):
                raise ValueError("task payload must be a JSON object")
            if payload.get("task_id") != expected_task_id:
                raise ValueError("task_id does not match its SQLite record key")
            payload["status"] = TaskStatus(payload["status"])
            payload["created_at"] = cls._datetime(payload["created_at"], "created_at")
            payload["updated_at"] = cls._datetime(payload["updated_at"], "updated_at")
            evidence = payload.get("evidence", [])
            if not isinstance(evidence, list):
                raise ValueError("evidence must be a list")
            restored_evidence = []
            for item in evidence:
                if not isinstance(item, dict):
                    raise ValueError("each evidence item must be an object")
                item = dict(item)
                item["captured_at"] = cls._datetime(item["captured_at"], "evidence.captured_at")
                restored_evidence.append(Evidence(**item))
            payload["evidence"] = restored_evidence
            task = Task(**payload)
            if not task.task_id or not task.mission_id:
                raise ValueError("task_id and mission_id must be non-empty")
            if not isinstance(task.metadata, dict):
                raise ValueError("metadata must be an object")
            return task
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise RuntimeError(
                f"Cannot restore persisted task {expected_task_id!r}; "
                "the record was retained for inspection."
            ) from exc

    def _restore(self) -> None:
        assert self._message_bus is not None
        restored: dict[str, Task] = {}
        revisions: dict[str, int] = {}
        for record in self._message_bus.load_task_records():
            task_id = record["task_id"]
            if record["schema_version"] != self.SCHEMA_VERSION:
                raise RuntimeError(
                    f"Unsupported task schema version {record['schema_version']} "
                    f"for {task_id}; record was retained."
                )
            task = self._deserialize(record["payload_json"], task_id)
            revision = record["revision"]
            if not isinstance(revision, int) or revision < 1:
                raise RuntimeError(f"Invalid persistence revision for task {task_id}.")
            restored[task_id] = task
            revisions[task_id] = revision
        self._tasks = restored
        self._revisions = revisions

    def _persist_create(self, task: Task) -> None:
        if self._message_bus is not None:
            self._revisions[task.task_id] = self._message_bus.save_task_record(
                task.task_id, self._serialize(task), schema_version=self.SCHEMA_VERSION
            )

    def _persist_update(self, task: Task) -> None:
        if self._message_bus is not None:
            revision = self._revisions[task.task_id]
            self._revisions[task.task_id] = self._message_bus.update_task_record(
                task.task_id,
                revision,
                self._serialize(task),
                schema_version=self.SCHEMA_VERSION,
            )

    @property
    def durable_persistence_enabled(self) -> bool:
        """Whether task lifecycle updates use the existing SQLite message bus."""
        return self._message_bus is not None

    def create(self, task: Task) -> Task:
        with self._lock:
            if task.task_id in self._tasks:
                raise ValueError(f"Task already exists: {task.task_id}")
            stored = deepcopy(task)
            self._persist_create(stored)
            self._tasks[stored.task_id] = stored
            return deepcopy(stored)

    def get(self, task_id: str) -> Task | None:
        with self._lock:
            task = self._tasks.get(task_id)
            return deepcopy(task) if task is not None else None

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
            current = self._tasks[task_id]
            if current.status not in {TaskStatus.CREATED, TaskStatus.QUEUED}:
                raise ValueError(f"Task {task_id} cannot be assigned from {current.status}.")
            if not self.dependencies_satisfied(task_id):
                raise ValueError(f"Task {task_id} has unsatisfied dependencies.")
            updated = deepcopy(current)
            updated.assigned_agent = agent_id
            updated.status = TaskStatus.ASSIGNED
            updated.updated_at = utc_now()
            self._persist_update(updated)
            self._tasks[task_id] = updated
            return deepcopy(updated)

    def transition(self, task_id: str, status: TaskStatus) -> Task:
        if not isinstance(status, TaskStatus):
            raise TypeError("status must be a TaskStatus value")
        with self._lock:
            current = self._tasks[task_id]
            if current.status in self.TERMINAL:
                raise ValueError(f"Task {task_id} is already terminal.")
            updated = deepcopy(current)
            updated.status = status
            updated.updated_at = utc_now()
            self._persist_update(updated)
            self._tasks[task_id] = updated
            return deepcopy(updated)


    def complete_with_result(
        self, task_id: str, *, result: dict[str, Any], message_id: str
    ) -> Task:
        """Persist a durable worker result and mark its assigned task complete atomically."""
        if not isinstance(result, dict):
            raise TypeError("worker result must be a dictionary")
        if not isinstance(message_id, str) or not message_id.strip():
            raise ValueError("message_id must be a non-empty string")
        # Reject non-JSON values before changing the in-memory task snapshot.
        json.dumps(result, ensure_ascii=False, allow_nan=False)
        with self._lock:
            current = self._tasks[task_id]
            if not isinstance(current.metadata, dict):
                raise ValueError(f"Task {task_id} metadata is not a dictionary.")
            existing = current.metadata.get("worker_execution", {})
            if current.status == TaskStatus.COMPLETED:
                if (
                    isinstance(existing, dict)
                    and existing.get("message_id") == message_id
                    and existing.get("result") == result
                ):
                    return deepcopy(current)
                raise ValueError(f"Task {task_id} is already completed with a different result.")
            if current.status not in {TaskStatus.ASSIGNED, TaskStatus.RUNNING}:
                raise ValueError(f"Task {task_id} cannot complete from {current.status.value}.")
            updated = deepcopy(current)
            updated.metadata["worker_execution"] = {
                "message_id": message_id,
                "durable_receipt": True,
                "result": deepcopy(result),
            }
            updated.status = TaskStatus.COMPLETED
            updated.updated_at = utc_now()
            self._persist_update(updated)
            self._tasks[task_id] = updated
            return deepcopy(updated)

    def block_with_result(
        self, task_id: str, *, result: dict[str, Any], message_id: str
    ) -> Task:
        """Persist a durable worker refusal and keep the task non-approvable."""
        if not isinstance(result, dict) or result.get("status") != "BLOCKED":
            raise ValueError("blocked worker result must have status BLOCKED")
        if not isinstance(message_id, str) or not message_id.strip():
            raise ValueError("message_id must be a non-empty string")
        json.dumps(result, ensure_ascii=False, allow_nan=False)
        with self._lock:
            current = self._tasks[task_id]
            if not isinstance(current.metadata, dict):
                raise ValueError(f"Task {task_id} metadata is not a dictionary.")
            existing = current.metadata.get("worker_execution", {})
            if current.status == TaskStatus.BLOCKED:
                if (
                    isinstance(existing, dict)
                    and existing.get("message_id") == message_id
                    and existing.get("result") == result
                ):
                    return deepcopy(current)
                raise ValueError(f"Task {task_id} is already blocked with a different result.")
            if current.status not in {TaskStatus.ASSIGNED, TaskStatus.RUNNING}:
                raise ValueError(f"Task {task_id} cannot be blocked from {current.status.value}.")
            updated = deepcopy(current)
            updated.metadata["worker_execution"] = {
                "message_id": message_id,
                "durable_receipt": True,
                "result": deepcopy(result),
            }
            updated.status = TaskStatus.BLOCKED
            updated.updated_at = utc_now()
            self._persist_update(updated)
            self._tasks[task_id] = updated
            return deepcopy(updated)

    def ready_tasks(self) -> list[Task]:
        with self._lock:
            return [
                deepcopy(task)
                for task in self._tasks.values()
                if task.status in {TaskStatus.CREATED, TaskStatus.QUEUED}
                and self.dependencies_satisfied(task.task_id)
            ]
