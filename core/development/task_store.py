"""Transactional SQLite persistence for truthful DGM-MAT development task states.

This store records task state and audit events. It does not execute code, grant
permissions, or certify success on its own. VERIFIED is accepted only with
passed validation and independent-QA evidence supplied by the caller.
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Iterator

from core.development.task_result import (
    DevelopmentTaskResult,
    TaskEvidence,
    TaskResultStatus,
)


_ALLOWED_TRANSITIONS: dict[TaskResultStatus, frozenset[TaskResultStatus]] = {
    TaskResultStatus.PLANNED: frozenset({
        TaskResultStatus.RUNNING,
        TaskResultStatus.BLOCKED,
        TaskResultStatus.NOT_IMPLEMENTED,
        TaskResultStatus.FAILED,
    }),
    TaskResultStatus.RUNNING: frozenset({
        TaskResultStatus.BLOCKED,
        TaskResultStatus.FAILED,
        TaskResultStatus.VERIFIED,
    }),
    TaskResultStatus.BLOCKED: frozenset({TaskResultStatus.PLANNED, TaskResultStatus.RUNNING}),
    TaskResultStatus.NOT_IMPLEMENTED: frozenset({TaskResultStatus.PLANNED}),
    TaskResultStatus.FAILED: frozenset({TaskResultStatus.PLANNED}),
    TaskResultStatus.VERIFIED: frozenset(),
}


class TaskStoreError(RuntimeError):
    """Base exception for durable task registry errors."""


class TaskNotFoundError(TaskStoreError):
    """Raised when a requested task does not exist."""


class InvalidTaskTransitionError(TaskStoreError):
    """Raised when a state transition is not permitted."""


class TaskStore:
    """Small local SQLite task registry with transactional state and audit events."""

    def __init__(self, database_path: str | Path | None = None) -> None:
        configured = database_path or os.getenv("DGM_TASK_STORE_PATH")
        if configured is None:
            configured = Path.home() / ".dgm-mat" / "development-tasks.sqlite3"
        self.database_path = Path(configured).expanduser().resolve()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(str(self.database_path), timeout=5.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        return connection

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        """Commit or roll back a connection scope, then always release the handle."""
        connection = self._connect()
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connection() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS development_tasks (
                    task_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    validation_passed INTEGER NOT NULL DEFAULT 0,
                    independent_qa_passed INTEGER NOT NULL DEFAULT 0,
                    commit_sha TEXT,
                    revision INTEGER NOT NULL DEFAULT 1,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS development_task_evidence (
                    task_id TEXT NOT NULL REFERENCES development_tasks(task_id) ON DELETE CASCADE,
                    ordinal INTEGER NOT NULL,
                    kind TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    reference TEXT NOT NULL,
                    detail TEXT NOT NULL,
                    PRIMARY KEY (task_id, ordinal)
                );
                CREATE TABLE IF NOT EXISTS development_task_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL REFERENCES development_tasks(task_id) ON DELETE CASCADE,
                    from_status TEXT,
                    to_status TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    evidence_json TEXT NOT NULL,
                    revision INTEGER NOT NULL,
                    occurred_at REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_development_task_events_task
                    ON development_task_events(task_id, event_id);
                """
            )

    @staticmethod
    def _encode_evidence(evidence: Iterable[TaskEvidence]) -> str:
        return json.dumps(
            [
                {
                    "kind": item.kind,
                    "outcome": item.outcome,
                    "reference": item.reference,
                    "detail": item.detail,
                }
                for item in evidence
            ],
            ensure_ascii=False,
            separators=(",", ":"),
        )

    @staticmethod
    def _decode_evidence(payload: str) -> tuple[TaskEvidence, ...]:
        items = json.loads(payload)
        return tuple(TaskEvidence(**item) for item in items)

    def create(self, result: DevelopmentTaskResult) -> DevelopmentTaskResult:
        if result.status is not TaskResultStatus.PLANNED:
            raise InvalidTaskTransitionError("New tasks must start in the planned state.")
        now = time.time()
        with self._connection() as connection:
            try:
                connection.execute(
                    """INSERT INTO development_tasks
                       (task_id, status, summary, validation_passed, independent_qa_passed,
                        commit_sha, revision, created_at, updated_at)
                       VALUES (?, ?, ?, 0, 0, ?, 1, ?, ?)""",
                    (result.task_id, result.status.value, result.summary, result.commit_sha, now, now),
                )
            except sqlite3.IntegrityError as exc:
                raise InvalidTaskTransitionError(f"Task '{result.task_id}' already exists.") from exc
            connection.execute(
                """INSERT INTO development_task_events
                   (task_id, from_status, to_status, summary, evidence_json, revision, occurred_at)
                   VALUES (?, NULL, ?, ?, '[]', 1, ?)""",
                (result.task_id, result.status.value, result.summary, now),
            )
        return self.get(result.task_id)

    def get(self, task_id: str) -> DevelopmentTaskResult:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM development_tasks WHERE task_id = ?", (task_id,)
            ).fetchone()
            if row is None:
                raise TaskNotFoundError(f"Task '{task_id}' was not found.")
            evidence_rows = connection.execute(
                """SELECT kind, outcome, reference, detail
                   FROM development_task_evidence WHERE task_id = ? ORDER BY ordinal""",
                (task_id,),
            ).fetchall()
        evidence = tuple(TaskEvidence(**dict(item)) for item in evidence_rows)
        return DevelopmentTaskResult(
            task_id=row["task_id"],
            status=TaskResultStatus(row["status"]),
            summary=row["summary"],
            evidence=evidence,
            validation_passed=bool(row["validation_passed"]),
            independent_qa_passed=bool(row["independent_qa_passed"]),
            commit_sha=row["commit_sha"],
        )

    def transition(
        self,
        task_id: str,
        status: TaskResultStatus,
        summary: str,
        *,
        evidence: Iterable[TaskEvidence] = (),
        validation_passed: bool = False,
        independent_qa_passed: bool = False,
        commit_sha: str | None = None,
        expected_revision: int | None = None,
    ) -> DevelopmentTaskResult:
        new_evidence = tuple(evidence)
        if not isinstance(status, TaskResultStatus):
            raise ValueError("status must be a TaskResultStatus value.")
        if not isinstance(summary, str) or not summary.strip():
            raise ValueError("summary must be a non-empty string.")
        now = time.time()
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM development_tasks WHERE task_id = ?", (task_id,)
            ).fetchone()
            if row is None:
                connection.rollback()
                raise TaskNotFoundError(f"Task '{task_id}' was not found.")
            current = TaskResultStatus(row["status"])
            revision = int(row["revision"])
            if expected_revision is not None and expected_revision != revision:
                connection.rollback()
                raise InvalidTaskTransitionError(
                    f"Stale task revision: expected {expected_revision}, current {revision}."
                )
            if status not in _ALLOWED_TRANSITIONS[current]:
                connection.rollback()
                raise InvalidTaskTransitionError(
                    f"Transition from '{current.value}' to '{status.value}' is not allowed."
                )
            # Constructing the contract enforces verification evidence before committing.
            result = DevelopmentTaskResult(
                task_id=task_id,
                status=status,
                summary=summary,
                evidence=new_evidence,
                validation_passed=validation_passed,
                independent_qa_passed=independent_qa_passed,
                commit_sha=commit_sha if commit_sha is not None else row["commit_sha"],
            )
            new_revision = revision + 1
            connection.execute(
                """UPDATE development_tasks
                   SET status = ?, summary = ?, validation_passed = ?,
                       independent_qa_passed = ?, commit_sha = ?, revision = ?, updated_at = ?
                   WHERE task_id = ?""",
                (
                    status.value, summary, int(validation_passed), int(independent_qa_passed),
                    result.commit_sha, new_revision, now, task_id,
                ),
            )
            connection.execute("DELETE FROM development_task_evidence WHERE task_id = ?", (task_id,))
            connection.executemany(
                """INSERT INTO development_task_evidence
                   (task_id, ordinal, kind, outcome, reference, detail)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                [
                    (task_id, index, item.kind, item.outcome, item.reference, item.detail)
                    for index, item in enumerate(new_evidence)
                ],
            )
            connection.execute(
                """INSERT INTO development_task_events
                   (task_id, from_status, to_status, summary, evidence_json, revision, occurred_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    task_id, current.value, status.value, summary,
                    self._encode_evidence(new_evidence), new_revision, now,
                ),
            )
            connection.commit()
        return self.get(task_id)

    def list_events(self, task_id: str) -> list[dict[str, object]]:
        with self._connection() as connection:
            exists = connection.execute(
                "SELECT 1 FROM development_tasks WHERE task_id = ?", (task_id,)
            ).fetchone()
            if exists is None:
                raise TaskNotFoundError(f"Task '{task_id}' was not found.")
            rows = connection.execute(
                """SELECT event_id, from_status, to_status, summary, evidence_json,
                          revision, occurred_at
                   FROM development_task_events WHERE task_id = ? ORDER BY event_id""",
                (task_id,),
            ).fetchall()
        return [
            {
                "event_id": row["event_id"],
                "from_status": row["from_status"],
                "to_status": row["to_status"],
                "summary": row["summary"],
                "evidence": json.loads(row["evidence_json"]),
                "revision": row["revision"],
                "occurred_at": row["occurred_at"],
            }
            for row in rows
        ]
