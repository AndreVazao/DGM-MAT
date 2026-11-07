"""Durable, single-claim queue for commands sent through authenticated browser UI."""
from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable


class BrowserOperatorQueueError(ValueError):
    pass


class BrowserOperatorQueue:
    """SQLite queue; expired in-flight sends require review and are never replayed."""

    def __init__(self, database_path: str | Path, *, lease_seconds: int = 180, mission_status_resolver: Callable[[str], str | None] | None = None) -> None:
        if not 30 <= lease_seconds <= 900:
            raise ValueError("lease_seconds must be between 30 and 900")
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.lease_seconds = lease_seconds
        self._mission_status_resolver = mission_status_resolver
        self._lock = threading.RLock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=10, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout=10000")
        connection.execute("PRAGMA journal_mode=WAL")
        return connection

    def _initialize(self) -> None:
        with self._lock, self._connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS browser_operator_tasks (
                    task_id TEXT PRIMARY KEY,
                    idempotency_key TEXT NOT NULL UNIQUE,
                    mission_id TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    conversation_url TEXT NOT NULL,
                    message TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    created_by TEXT NOT NULL DEFAULT 'mission-engine',
                    approved_by TEXT,
                    approval_required INTEGER NOT NULL DEFAULT 1,
                    claimed_by TEXT,
                    claim_token TEXT,
                    lease_until TEXT,
                    result_json TEXT,
                    error TEXT
                )
            """)
            columns = {row["name"] for row in db.execute("PRAGMA table_info(browser_operator_tasks)").fetchall()}
            if "created_by" not in columns:
                db.execute("ALTER TABLE browser_operator_tasks ADD COLUMN created_by TEXT NOT NULL DEFAULT 'mission-engine'")
            if "approved_by" not in columns:
                db.execute("ALTER TABLE browser_operator_tasks ADD COLUMN approved_by TEXT")
            if "approval_required" not in columns:
                db.execute("ALTER TABLE browser_operator_tasks ADD COLUMN approval_required INTEGER NOT NULL DEFAULT 1")
                db.execute("UPDATE browser_operator_tasks SET approval_required=0 WHERE created_by='mission-engine' AND approved_by='mission-engine' AND status IN ('queued','claimed','completed','unverified','needs_review')")
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_browser_operator_pending
                ON browser_operator_tasks(status, provider, created_at)
            """)

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _decode(row: sqlite3.Row | None) -> dict[str, Any] | None:
        if row is None:
            return None
        item = dict(row)
        item["approval_required"] = bool(item.get("approval_required", 1))
        raw = item.pop("result_json", None)
        try:
            item["result"] = json.loads(raw) if raw else None
        except (TypeError, json.JSONDecodeError):
            item["result"] = None
        return item

    def enqueue(
        self, *, idempotency_key: str, mission_id: str, provider: str,
        source_id: str, conversation_url: str, message: str,
        approval_required: bool = True, created_by: str = "mission-engine",
    ) -> dict[str, Any]:
        values = (idempotency_key, mission_id, provider, source_id, conversation_url, message, created_by)
        if any(not isinstance(value, str) or not value.strip() for value in values):
            raise BrowserOperatorQueueError("All task identity and content fields must be non-empty strings")
        if len(idempotency_key) > 200 or len(mission_id) > 80 or len(source_id) > 200 or len(created_by) > 200:
            raise BrowserOperatorQueueError("Task identity field exceeds its limit")
        if provider not in {"chatgpt", "gemini", "grok", "deepseek", "qwen"}:
            raise BrowserOperatorQueueError("Unsupported browser provider")
        parent_status = None
        if self._mission_status_resolver is not None:
            try:
                raw_status = self._mission_status_resolver(mission_id)
                parent_status = str(getattr(raw_status, "value", raw_status)).upper() if raw_status is not None else None
            except Exception:
                parent_status = None
        if parent_status is None:
            raise BrowserOperatorQueueError("Parent mission checkpoint is missing or unavailable")
        if parent_status in {"COMPLETED", "CANCELLED", "FAILED"}:
            raise BrowserOperatorQueueError("A terminal mission cannot receive a browser task")
        if not approval_required and parent_status != "RUNNING":
            raise BrowserOperatorQueueError("Approval bypass requires a freshly verified RUNNING parent mission")
        if len(conversation_url) > 2048 or len(message) > 30000:
            raise BrowserOperatorQueueError("Conversation URL or message exceeds its limit")
        now = self._now().isoformat()
        task_id = "browser_" + uuid.uuid4().hex
        status = "pending_approval" if approval_required else "queued"
        with self._lock, self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute(
                "SELECT * FROM browser_operator_tasks WHERE idempotency_key=?",
                (idempotency_key,),
            ).fetchone()
            if existing:
                existing_item = self._decode(existing) or {}
                expected = (mission_id, provider, source_id, conversation_url, message, bool(approval_required))
                actual = tuple(existing_item.get(key) for key in ("mission_id", "provider", "source_id", "conversation_url", "message", "approval_required"))
                if actual != expected:
                    db.rollback()
                    raise BrowserOperatorQueueError("Idempotency key is already bound to a different task envelope")
                db.commit()
                return existing_item
            approved_by = created_by if not approval_required else None
            db.execute("""
                INSERT INTO browser_operator_tasks (
                    task_id,idempotency_key,mission_id,provider,source_id,conversation_url,
                    message,status,created_at,updated_at,created_by,approved_by,approval_required
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (task_id, idempotency_key, mission_id, provider, source_id,
                  conversation_url, message, status, now, now, created_by, approved_by,
                  int(bool(approval_required))))
            row = db.execute(
                "SELECT * FROM browser_operator_tasks WHERE task_id=?", (task_id,)
            ).fetchone()
            db.commit()
            return self._decode(row) or {}

    def approve(self, task_id: str, *, operator: str) -> bool:
        if not operator or len(operator) > 200:
            raise BrowserOperatorQueueError("A valid operator identity is required")
        with self._lock, self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            changed = db.execute("""
                UPDATE browser_operator_tasks
                SET status='queued', approved_by=?, updated_at=?
                WHERE task_id=? AND status='pending_approval'
            """, (operator, self._now().isoformat(), task_id)).rowcount
            db.commit()
            return changed == 1

    def claim_next(self, *, provider: str, worker_id: str) -> dict[str, Any] | None:
        if provider not in {"chatgpt", "gemini", "grok", "deepseek", "qwen"} or not worker_id or len(worker_id) > 200:
            raise BrowserOperatorQueueError("Provider and worker identity are required")
        now = self._now()
        token = uuid.uuid4().hex
        with self._lock, self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            # A timed-out claim is not retried: the previous browser click may have
            # succeeded even if its acknowledgement was lost.
            db.execute("""
                UPDATE browser_operator_tasks
                SET status='needs_review', updated_at=?,
                    error='claim_lease_expired; automatic replay prohibited'
                WHERE status='claimed' AND lease_until IS NOT NULL AND lease_until < ?
            """, (now.isoformat(), now.isoformat()))
            row = db.execute("""
                SELECT task_id FROM browser_operator_tasks
                WHERE status='queued' AND provider=?
                ORDER BY created_at, task_id LIMIT 1
            """, (provider,)).fetchone()
            if row is None:
                db.commit()
                return None
            lease_until = (now + timedelta(seconds=self.lease_seconds)).isoformat()
            changed = db.execute("""
                UPDATE browser_operator_tasks
                SET status='claimed', claimed_by=?, claim_token=?, lease_until=?, updated_at=?
                WHERE task_id=? AND status='queued'
            """, (worker_id, token, lease_until, now.isoformat(), row["task_id"])).rowcount
            if changed != 1:
                db.rollback()
                return None
            claimed = db.execute(
                "SELECT * FROM browser_operator_tasks WHERE task_id=?", (row["task_id"],)
            ).fetchone()
            db.commit()
            result = self._decode(claimed) or {}
            result["claim_token"] = token
            return result

    def complete(
        self, task_id: str, *, worker_id: str, claim_token: str,
        result: dict[str, Any], status: str = "completed",
    ) -> bool:
        if status not in {"completed", "unverified"}:
            raise BrowserOperatorQueueError("Result status must be completed or unverified")
        encoded = json.dumps(result, ensure_ascii=False, sort_keys=True)
        if len(encoded) > 100000:
            raise BrowserOperatorQueueError("Browser result exceeds 100 KB")
        with self._lock, self._connect() as db:
            changed = db.execute("""
                UPDATE browser_operator_tasks
                SET status=?, result_json=?, updated_at=?, lease_until=NULL, claim_token=NULL
                WHERE task_id=? AND status='claimed' AND claimed_by=? AND claim_token=?
            """, (status, encoded, self._now().isoformat(), task_id, worker_id, claim_token)).rowcount
            return changed == 1

    def fail(
        self, task_id: str, *, worker_id: str, claim_token: str,
        reason: str, blocked: bool = False,
    ) -> bool:
        safe_reason = str(reason).strip()[:1000]
        if not safe_reason:
            raise BrowserOperatorQueueError("A failure reason is required")
        status = "blocked" if blocked else "failed"
        with self._lock, self._connect() as db:
            changed = db.execute("""
                UPDATE browser_operator_tasks
                SET status=?, error=?, updated_at=?, lease_until=NULL, claim_token=NULL
                WHERE task_id=? AND status='claimed' AND claimed_by=? AND claim_token=?
            """, (status, safe_reason, self._now().isoformat(), task_id, worker_id, claim_token)).rowcount
            return changed == 1

    def get(self, task_id: str) -> dict[str, Any] | None:
        with self._connect() as db:
            return self._decode(db.execute(
                "SELECT * FROM browser_operator_tasks WHERE task_id=?", (task_id,)
            ).fetchone())

    def list_tasks(self, *, limit: int = 50) -> list[dict[str, Any]]:
        if not 1 <= limit <= 200:
            raise ValueError("limit must be between 1 and 200")
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM browser_operator_tasks ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        items = [self._decode(row) or {} for row in rows]
        for item in items:
            item.pop("claim_token", None)
        return items
