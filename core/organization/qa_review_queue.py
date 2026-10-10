"""Durable, auditable work queue for specialist QA review requests.

Queue state is separate from message delivery receipts. A message being received
or handled never marks a review complete. Completion requires an explicit review
outcome and recorded evidence of checks actually performed.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any


STATUSES = frozenset({"PENDING", "IN_PROGRESS", "BLOCKED", "COMPLETED", "REJECTED"})
_TERMINAL = frozenset({"COMPLETED", "REJECTED"})


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class QAReviewQueue:
    """SQLite queue with idempotent intake and guarded state transitions."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path).expanduser().resolve() if db_path is not None else None
        if self.db_path is None:
            target = ":memory:"
        else:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            target = str(self.db_path)
        self._lock = RLock()
        self._conn = sqlite3.connect(target, timeout=5.0, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA busy_timeout=5000")
        if self.db_path is not None:
            self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("""CREATE TABLE IF NOT EXISTS qa_review_work_items (
            work_item_id TEXT PRIMARY KEY,
            correlation_id TEXT NOT NULL UNIQUE,
            source_message_id TEXT NOT NULL,
            mission_id TEXT,
            subject TEXT NOT NULL,
            request_body TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT NOT NULL,
            owner_id TEXT,
            attempts INTEGER NOT NULL DEFAULT 0,
            max_attempts INTEGER NOT NULL DEFAULT 3,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            last_error TEXT,
            review_outcome TEXT,
            evidence_json TEXT NOT NULL DEFAULT '[]',
            tests_executed_json TEXT NOT NULL DEFAULT '[]'
        )""")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_qa_review_status_created ON qa_review_work_items(status, created_at)")
        self._conn.commit()

    @staticmethod
    def _row(row: sqlite3.Row) -> dict[str, Any]:
        item = dict(row)
        item["evidence"] = json.loads(item.pop("evidence_json"))
        item["tests_executed"] = json.loads(item.pop("tests_executed_json"))
        return item

    def enqueue(self, *, correlation_id: str, source_message_id: str, mission_id: str | None,
                subject: str, request_body: str, priority: str, owner_id: str | None = None,
                max_attempts: int = 3) -> dict[str, Any]:
        values = (correlation_id, source_message_id, mission_id, subject, request_body, priority)
        if any(not isinstance(v, str) or not v.strip() for v in (correlation_id, source_message_id, subject, request_body, priority)):
            raise ValueError("correlation_id, source_message_id, subject, request_body and priority are required")
        if max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        now = _now()
        with self._lock, self._conn:
            existing = self._conn.execute("SELECT * FROM qa_review_work_items WHERE correlation_id=?", (correlation_id,)).fetchone()
            if existing:
                if (existing["source_message_id"], existing["subject"], existing["request_body"]) != (source_message_id, subject, request_body):
                    raise ValueError("Conflicting review request for existing correlation_id")
                return self._row(existing)
            item_id = f"qa-review:{correlation_id}"
            self._conn.execute("""INSERT INTO qa_review_work_items
                (work_item_id, correlation_id, source_message_id, mission_id, subject, request_body,
                 priority, status, owner_id, attempts, max_attempts, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'PENDING', ?, 0, ?, ?, ?)""",
                (item_id, *values, owner_id, max_attempts, now, now))
            row = self._conn.execute("SELECT * FROM qa_review_work_items WHERE work_item_id=?", (item_id,)).fetchone()
        return self._row(row)

    def get(self, work_item_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._conn.execute("SELECT * FROM qa_review_work_items WHERE work_item_id=? OR correlation_id=?", (work_item_id, work_item_id)).fetchone()
        return self._row(row) if row else None

    def list_items(self, *, status: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        if limit < 1 or limit > 1000:
            raise ValueError("limit must be between 1 and 1000")
        if status is not None and status not in STATUSES:
            raise ValueError(f"Unsupported status: {status}")
        query = "SELECT * FROM qa_review_work_items"
        params: tuple[Any, ...] = ()
        if status:
            query += " WHERE status=?"
            params = (status,)
        query += " ORDER BY created_at ASC LIMIT ?"
        with self._lock:
            rows = self._conn.execute(query, (*params, limit)).fetchall()
        return [self._row(row) for row in rows]

    def claim(self, work_item_id: str, owner_id: str) -> dict[str, Any]:
        if not owner_id or not owner_id.strip():
            raise ValueError("owner_id is required")
        now = _now()
        with self._lock, self._conn:
            row = self._conn.execute("SELECT * FROM qa_review_work_items WHERE work_item_id=? OR correlation_id=?", (work_item_id, work_item_id)).fetchone()
            if row is None:
                raise KeyError(work_item_id)
            if row["status"] in _TERMINAL:
                raise ValueError(f"Cannot claim terminal work item: {row['status']}")
            if row["status"] == "IN_PROGRESS" and row["owner_id"] != owner_id:
                raise ValueError("Work item is already claimed by another owner")
            attempts = int(row["attempts"]) + (0 if row["status"] == "IN_PROGRESS" and row["owner_id"] == owner_id else 1)
            if attempts > int(row["max_attempts"]):
                raise ValueError("Maximum review attempts exceeded; explicit supervisor intervention required")
            self._conn.execute("UPDATE qa_review_work_items SET status='IN_PROGRESS', owner_id=?, attempts=?, updated_at=?, last_error=NULL WHERE work_item_id=?", (owner_id, attempts, now, row["work_item_id"]))
            updated = self._conn.execute("SELECT * FROM qa_review_work_items WHERE work_item_id=?", (row["work_item_id"],)).fetchone()
        return self._row(updated)

    def block(self, work_item_id: str, *, reason: str, owner_id: str | None = None) -> dict[str, Any]:
        if not reason or not reason.strip():
            raise ValueError("A blocking reason is required")
        return self._transition(work_item_id, "BLOCKED", owner_id=owner_id, last_error=reason.strip())

    def retry(self, work_item_id: str, *, reason: str) -> dict[str, Any]:
        if not reason or not reason.strip():
            raise ValueError("A retry reason is required")
        with self._lock, self._conn:
            row = self._find(work_item_id)
            if row is None:
                raise KeyError(work_item_id)
            if row["status"] != "BLOCKED":
                raise ValueError("Only BLOCKED work items can be returned to PENDING")
            if int(row["attempts"]) >= int(row["max_attempts"]):
                raise ValueError("Maximum review attempts reached; supervisor intervention required")
            self._conn.execute("UPDATE qa_review_work_items SET status='PENDING', owner_id=NULL, last_error=?, updated_at=? WHERE work_item_id=?", (reason.strip(), _now(), row["work_item_id"]))
            updated = self._find(row["work_item_id"])
        return self._row(updated)

    def complete(self, work_item_id: str, *, owner_id: str, review_outcome: str,
                 tests_executed: list[dict[str, Any]], evidence: list[dict[str, Any]]) -> dict[str, Any]:
        if not owner_id or not owner_id.strip() or not review_outcome or not review_outcome.strip():
            raise ValueError("owner_id and explicit review_outcome are required")
        if not isinstance(tests_executed, list) or not tests_executed:
            raise ValueError("Completion requires at least one recorded test/check actually executed")
        if not isinstance(evidence, list) or not evidence:
            raise ValueError("Completion requires evidence records")
        if any(not isinstance(x, dict) or not str(x.get("name", "")).strip() or not str(x.get("result", "")).strip() for x in tests_executed):
            raise ValueError("Each executed test requires non-empty name and result")
        if any(not isinstance(x, dict) or not str(x.get("source", "")).strip() or not str(x.get("summary", "")).strip() for x in evidence):
            raise ValueError("Each evidence item requires non-empty source and summary")
        with self._lock, self._conn:
            row = self._find(work_item_id)
            if row is None:
                raise KeyError(work_item_id)
            if row["status"] != "IN_PROGRESS" or row["owner_id"] != owner_id:
                raise ValueError("Only the current owner can complete an IN_PROGRESS review")
            self._conn.execute("""UPDATE qa_review_work_items SET status='COMPLETED', review_outcome=?,
                tests_executed_json=?, evidence_json=?, updated_at=? WHERE work_item_id=?""",
                (review_outcome.strip(), json.dumps(tests_executed, ensure_ascii=False), json.dumps(evidence, ensure_ascii=False), _now(), row["work_item_id"]))
            updated = self._find(row["work_item_id"])
        return self._row(updated)

    def reject(self, work_item_id: str, *, owner_id: str, reason: str) -> dict[str, Any]:
        if not owner_id or not owner_id.strip() or not reason or not reason.strip():
            raise ValueError("owner_id and rejection reason are required")
        return self._transition(work_item_id, "REJECTED", owner_id=owner_id, last_error=reason.strip(), require_owner=True)

    def _find(self, key: str):
        return self._conn.execute("SELECT * FROM qa_review_work_items WHERE work_item_id=? OR correlation_id=?", (key, key)).fetchone()

    def _transition(self, key: str, status: str, *, owner_id: str | None, last_error: str | None, require_owner: bool = False) -> dict[str, Any]:
        with self._lock, self._conn:
            row = self._find(key)
            if row is None:
                raise KeyError(key)
            if row["status"] in _TERMINAL:
                raise ValueError(f"Cannot change terminal work item: {row['status']}")
            if require_owner and (row["status"] != "IN_PROGRESS" or row["owner_id"] != owner_id):
                raise ValueError("Only the current owner can reject an IN_PROGRESS review")
            self._conn.execute("UPDATE qa_review_work_items SET status=?, last_error=?, updated_at=? WHERE work_item_id=?", (status, last_error, _now(), row["work_item_id"]))
            updated = self._find(row["work_item_id"])
        return self._row(updated)

    def close(self) -> None:
        with self._lock:
            self._conn.close()
