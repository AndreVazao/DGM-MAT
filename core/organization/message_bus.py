"""Durable SQLite-backed internal message bus for DGM-MAT agents.

With no path, the bus uses a private in-memory SQLite database for tests and
ephemeral callers. Supplying a database path enables cross-instance/restart
persistence. Delivery is at-least-once: consumers should make handlers
idempotent because a process can stop after handling but before marking read.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Any

from .models import Evidence, Message, MessagePriority


def _json_default(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "value"):
        return value.value
    raise TypeError(f"Cannot serialize {type(value).__name__}")


def _dt(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


class InternalMessageBus:
    """Thread-safe inbox/outbox with optional durable cross-process storage."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path).expanduser().resolve() if db_path is not None else None
        if self.db_path is not None:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            connect_target = str(self.db_path)
        else:
            connect_target = ":memory:"
        self._lock = RLock()
        self._conn = sqlite3.connect(
            connect_target, timeout=5.0, check_same_thread=False
        )
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA busy_timeout=5000")
        if self.db_path is not None:
            self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS organization_messages (
                message_id TEXT PRIMARY KEY,
                sender_id TEXT NOT NULL,
                recipient_id TEXT NOT NULL,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                task_id TEXT,
                mission_id TEXT,
                priority TEXT NOT NULL,
                evidence_json TEXT NOT NULL,
                requires_response INTEGER NOT NULL,
                correlation_id TEXT,
                created_at TEXT NOT NULL,
                read_at TEXT
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS organization_dispatch_receipts (
                message_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                status TEXT NOT NULL,
                result_json TEXT NOT NULL,
                dispatched_at TEXT NOT NULL,
                FOREIGN KEY(message_id) REFERENCES organization_messages(message_id)
            )
            """
        )
        self._conn.commit()

    @staticmethod
    def _serialize(message: Message) -> tuple:
        return (
            message.message_id,
            message.sender_id,
            message.recipient_id,
            message.subject,
            message.body,
            message.task_id,
            message.mission_id,
            message.priority.value,
            json.dumps([asdict(item) for item in message.evidence], default=_json_default),
            int(message.requires_response),
            message.correlation_id,
            message.created_at.isoformat(),
            message.read_at.isoformat() if message.read_at else None,
        )

    @staticmethod
    def _deserialize(row: sqlite3.Row) -> Message:
        evidence_data = json.loads(row["evidence_json"])
        evidence = []
        for item in evidence_data:
            item["captured_at"] = _dt(item.get("captured_at")) or datetime.now().astimezone()
            evidence.append(Evidence(**item))
        return Message(
            sender_id=row["sender_id"],
            recipient_id=row["recipient_id"],
            subject=row["subject"],
            body=row["body"],
            message_id=row["message_id"],
            task_id=row["task_id"],
            mission_id=row["mission_id"],
            priority=MessagePriority(row["priority"]),
            evidence=evidence,
            requires_response=bool(row["requires_response"]),
            correlation_id=row["correlation_id"],
            created_at=_dt(row["created_at"]) or datetime.now().astimezone(),
            read_at=_dt(row["read_at"]),
        )

    def send(self, message: Message) -> str:
        with self._lock, self._conn:
            existing = self._conn.execute(
                "SELECT sender_id, recipient_id, subject, body FROM organization_messages WHERE message_id=?",
                (message.message_id,),
            ).fetchone()
            if existing is not None:
                expected = (message.sender_id, message.recipient_id, message.subject, message.body)
                actual = tuple(existing[key] for key in ("sender_id", "recipient_id", "subject", "body"))
                if actual != expected:
                    raise ValueError(f"Conflicting message_id: {message.message_id}")
                return message.message_id
            self._conn.execute(
                """INSERT INTO organization_messages
                (message_id, sender_id, recipient_id, subject, body, task_id, mission_id,
                 priority, evidence_json, requires_response, correlation_id, created_at, read_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                self._serialize(message),
            )
        return message.message_id

    def receive(
        self,
        agent_id: str,
        *,
        priority: MessagePriority | None = None,
        unread_only: bool = False,
    ) -> list[Message]:
        clauses = ["recipient_id=?"]
        params: list[Any] = [agent_id]
        if priority is not None:
            clauses.append("priority=?")
            params.append(priority.value)
        if unread_only:
            clauses.append("read_at IS NULL")
        query = "SELECT * FROM organization_messages WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at ASC, rowid ASC"
        with self._lock:
            rows = self._conn.execute(query, params).fetchall()
        return [self._deserialize(row) for row in rows]

    def mark_read(self, agent_id: str, message_id: str) -> None:
        with self._lock, self._conn:
            cursor = self._conn.execute(
                """UPDATE organization_messages SET read_at=?
                WHERE recipient_id=? AND message_id=? AND read_at IS NULL""",
                (datetime.now().astimezone().isoformat(), agent_id, message_id),
            )
            if cursor.rowcount == 0:
                exists = self._conn.execute(
                    "SELECT 1 FROM organization_messages WHERE recipient_id=? AND message_id=?",
                    (agent_id, message_id),
                ).fetchone()
                if exists is None:
                    raise KeyError(message_id)

    def outbox(self, agent_id: str) -> list[Message]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM organization_messages WHERE sender_id=? ORDER BY created_at ASC, rowid ASC",
                (agent_id,),
            ).fetchall()
        return [self._deserialize(row) for row in rows]

    def counts(self) -> dict[str, int]:
        with self._lock:
            inboxes = self._conn.execute("SELECT COUNT(*) FROM organization_messages").fetchone()[0]
            outboxes = self._conn.execute("SELECT COUNT(*) FROM organization_messages").fetchone()[0]
        return {"inboxes": int(inboxes), "outboxes": int(outboxes)}

    def complete_dispatch(self, agent_id: str, message_id: str, result: Any) -> None:
        """Persist a JSON-safe handler receipt and acknowledge the message atomically."""
        result_json = json.dumps(result, ensure_ascii=False, allow_nan=False)
        read_at = datetime.now().astimezone().isoformat()
        with self._lock, self._conn:
            message = self._conn.execute(
                "SELECT recipient_id FROM organization_messages WHERE message_id=?",
                (message_id,),
            ).fetchone()
            if message is None or message["recipient_id"] != agent_id:
                raise KeyError(message_id)
            receipt = self._conn.execute(
                "SELECT agent_id, result_json FROM organization_dispatch_receipts WHERE message_id=?",
                (message_id,),
            ).fetchone()
            if receipt is not None and receipt["agent_id"] != agent_id:
                raise ValueError(f"Conflicting dispatch receipt: {message_id}")
            if receipt is None:
                self._conn.execute(
                    """INSERT INTO organization_dispatch_receipts
                    (message_id, agent_id, status, result_json, dispatched_at)
                    VALUES (?, ?, 'HANDLED', ?, ?)""",
                    (message_id, agent_id, result_json, read_at),
                )
            self._conn.execute(
                "UPDATE organization_messages SET read_at=COALESCE(read_at, ?) WHERE message_id=? AND recipient_id=?",
                (read_at, message_id, agent_id),
            )

    def get_dispatch_result(self, message_id: str) -> dict[str, Any] | None:
        """Return a durable handler receipt without exposing arbitrary Python objects."""
        with self._lock:
            row = self._conn.execute(
                "SELECT message_id, agent_id, status, result_json, dispatched_at "
                "FROM organization_dispatch_receipts WHERE message_id=?",
                (message_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "message_id": row["message_id"],
            "agent_id": row["agent_id"],
            "status": row["status"],
            "result": json.loads(row["result_json"]),
            "dispatched_at": row["dispatched_at"],
        }

    def close(self) -> None:
        with self._lock:
            self._conn.close()
