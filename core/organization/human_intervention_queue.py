# Path: C:\\ProgramasGodMode\\DGM-MAT\\core\\organization\\human_intervention_queue.py
"""Durable, single-use human handoffs for mission steps.

This store contains operational metadata only. It must never receive passwords,
OTP codes, session cookies, CAPTCHA answers, provider prompts, or other secrets.
It is deliberately not exposed through HTTP/WebSocket until global API auth and
device pairing are complete.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


_ACTIVE_STATUSES = (
    "PENDING",
    "NOTIFIED",
    "WAITING_FOR_DEVICE",
    "WAITING_FOR_USER",
    "RESPONSE_RECEIVED",
    "VERIFYING",
)
_DECISIONS = {"APPROVE", "REJECT", "CANCEL", "NEED_CONTEXT"}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


class HumanInterventionQueue:
    """SQLite-backed human intervention queue with restart-safe single-use decisions."""

    def __init__(self, database_path: str | Path, *, timeout_seconds: float = 5.0) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.timeout_seconds = timeout_seconds
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            str(self.database_path),
            timeout=self.timeout_seconds,
            isolation_level=None,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        return connection

    def _initialize(self) -> None:
        with closing(self._connect()) as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("""
                CREATE TABLE IF NOT EXISTS human_intervention_requests (
                    request_id TEXT PRIMARY KEY,
                    mission_id TEXT NOT NULL,
                    step_id TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    instructions TEXT NOT NULL,
                    risk TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    decision TEXT,
                    decided_by TEXT,
                    decided_at TEXT,
                    version INTEGER NOT NULL DEFAULT 1
                )
            """)
            connection.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS ux_human_intervention_active_step
                ON human_intervention_requests(mission_id, step_id)
                WHERE status IN (
                    'PENDING', 'NOTIFIED', 'WAITING_FOR_DEVICE',
                    'WAITING_FOR_USER', 'RESPONSE_RECEIVED', 'VERIFYING'
                )
            """)
            connection.execute("""
                CREATE INDEX IF NOT EXISTS ix_human_intervention_status_expiry
                ON human_intervention_requests(status, expires_at)
            """)

    @staticmethod
    def _validate_text(name: str, value: str, max_length: int) -> str:
        if not isinstance(value, str):
            raise ValueError(f"{name} must be text")
        normalized = value.strip()
        if not normalized:
            raise ValueError(f"{name} is required")
        if len(normalized) > max_length:
            raise ValueError(f"{name} exceeds {max_length} characters")
        return normalized

    def create_request(
        self,
        *,
        mission_id: str,
        step_id: str,
        reason: str,
        instructions: str,
        risk: str = "MEDIUM",
        ttl_seconds: int = 900,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        """Persist a bounded handoff before any notification is sent."""
        mission_id = self._validate_text("mission_id", mission_id, 128)
        step_id = self._validate_text("step_id", step_id, 128)
        reason = self._validate_text("reason", reason, 500)
        instructions = self._validate_text("instructions", instructions, 1500)
        risk = self._validate_text("risk", risk, 32).upper()
        if risk not in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}:
            raise ValueError("risk must be LOW, MEDIUM, HIGH, or CRITICAL")
        if type(ttl_seconds) is not int or not 1 <= ttl_seconds <= 86400:
            raise ValueError("ttl_seconds must be between 1 and 86400")
        created = now or _utc_now()
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        expires = created + timedelta(seconds=ttl_seconds)
        request_id = str(uuid4())
        values = (
            request_id, mission_id, step_id, reason, instructions, risk,
            "WAITING_FOR_USER", _iso(created), _iso(expires),
        )
        try:
            with closing(self._connect()) as connection:
                connection.execute(
                    """INSERT INTO human_intervention_requests
                    (request_id, mission_id, step_id, reason, instructions, risk,
                     status, created_at, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    values,
                )
        except sqlite3.IntegrityError as exc:
            raise ValueError("An active human intervention already exists for this mission step") from exc
        return self.get_request(request_id)  # type: ignore[return-value]

    def get_request(self, request_id: str, *, now: datetime | None = None) -> dict[str, Any] | None:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT * FROM human_intervention_requests WHERE request_id = ?",
                (request_id,),
            ).fetchone()
        if row is None:
            return None
        result = dict(row)
        if result["status"] in _ACTIVE_STATUSES and result["expires_at"] <= _iso(now or _utc_now()):
            self._expire_one(request_id, now=now)
            with closing(self._connect()) as connection:
                row = connection.execute(
                    "SELECT * FROM human_intervention_requests WHERE request_id = ?",
                    (request_id,),
                ).fetchone()
            result = dict(row)
        return result

    def list_pending(self, *, mission_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        if type(limit) is not int or not 1 <= limit <= 500:
            raise ValueError("limit must be between 1 and 500")
        self.expire_due()
        where = "status IN (" + ",".join("?" for _ in _ACTIVE_STATUSES) + ")"
        params: list[Any] = list(_ACTIVE_STATUSES)
        if mission_id is not None:
            where += " AND mission_id = ?"
            params.append(self._validate_text("mission_id", mission_id, 128))
        params.append(limit)
        with closing(self._connect()) as connection:
            rows = connection.execute(
                f"SELECT * FROM human_intervention_requests WHERE {where} ORDER BY created_at LIMIT ?",
                params,
            ).fetchall()
        return [dict(row) for row in rows]

    def submit_decision(
        self,
        request_id: str,
        *,
        mission_id: str,
        step_id: str,
        decision: str,
        actor_id: str,
        now: datetime | None = None,
    ) -> bool:
        """Atomically consume a decision once; a duplicate/stale/wrong-step reply fails."""
        mission_id = self._validate_text("mission_id", mission_id, 128)
        step_id = self._validate_text("step_id", step_id, 128)
        actor_id = self._validate_text("actor_id", actor_id, 128)
        normalized_decision = self._validate_text("decision", decision, 32).upper()
        if normalized_decision not in _DECISIONS:
            raise ValueError("Unsupported decision")
        timestamp = _iso(now or _utc_now())
        with closing(self._connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM human_intervention_requests WHERE request_id = ?",
                (request_id,),
            ).fetchone()
            if row is None or row["mission_id"] != mission_id or row["step_id"] != step_id:
                connection.rollback()
                return False
            if row["status"] not in {"WAITING_FOR_USER", "WAITING_FOR_DEVICE", "NOTIFIED", "PENDING"}:
                connection.rollback()
                return False
            if row["expires_at"] <= timestamp:
                connection.execute(
                    """UPDATE human_intervention_requests SET status='EXPIRED',
                    version=version+1 WHERE request_id=? AND status=?""",
                    (request_id, row["status"]),
                )
                connection.commit()
                return False
            updated = connection.execute(
                """UPDATE human_intervention_requests
                SET status='RESPONSE_RECEIVED', decision=?, decided_by=?, decided_at=?,
                    version=version+1
                WHERE request_id=? AND status=? AND version=?""",
                (
                    normalized_decision, actor_id, timestamp,
                    request_id, row["status"], row["version"],
                ),
            )
            if updated.rowcount != 1:
                connection.rollback()
                return False
            connection.commit()
            return True

    def mark_verifying(self, request_id: str, *, now: datetime | None = None) -> bool:
        """Move an accepted response into verification; does not itself resume a mission."""
        timestamp = _iso(now or _utc_now())
        with closing(self._connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT status, expires_at, version FROM human_intervention_requests WHERE request_id=?",
                (request_id,),
            ).fetchone()
            if row is None or row["status"] != "RESPONSE_RECEIVED":
                connection.rollback()
                return False
            if row["expires_at"] <= timestamp:
                connection.execute(
                    "UPDATE human_intervention_requests SET status='EXPIRED', version=version+1 WHERE request_id=? AND version=?",
                    (request_id, row["version"]),
                )
                connection.commit()
                return False
            updated = connection.execute(
                """UPDATE human_intervention_requests SET status='VERIFYING', version=version+1
                WHERE request_id=? AND status='RESPONSE_RECEIVED' AND version=?""",
                (request_id, row["version"]),
            )
            if updated.rowcount != 1:
                connection.rollback()
                return False
            connection.commit()
            return True

    def finalize(self, request_id: str, *, outcome: str) -> bool:
        """Close a verifying handoff after the caller independently checked real state."""
        if outcome not in {"RESUMED", "CANCELLED", "BLOCKED"}:
            raise ValueError("outcome must be RESUMED, CANCELLED, or BLOCKED")
        with closing(self._connect()) as connection:
            updated = connection.execute(
                """UPDATE human_intervention_requests SET status=?, version=version+1
                WHERE request_id=? AND status='VERIFYING'""",
                (outcome, request_id),
            )
            return updated.rowcount == 1

    def expire_due(self, *, now: datetime | None = None) -> int:
        timestamp = _iso(now or _utc_now())
        placeholders = ",".join("?" for _ in _ACTIVE_STATUSES)
        with closing(self._connect()) as connection:
            result = connection.execute(
                f"""UPDATE human_intervention_requests
                SET status='EXPIRED', version=version+1
                WHERE status IN ({placeholders}) AND expires_at <= ?""",
                (*_ACTIVE_STATUSES, timestamp),
            )
            return result.rowcount

    def _expire_one(self, request_id: str, *, now: datetime | None = None) -> None:
        timestamp = _iso(now or _utc_now())
        placeholders = ",".join("?" for _ in _ACTIVE_STATUSES)
        with closing(self._connect()) as connection:
            connection.execute(
                f"""UPDATE human_intervention_requests SET status='EXPIRED', version=version+1
                WHERE request_id=? AND status IN ({placeholders}) AND expires_at <= ?""",
                (request_id, *_ACTIVE_STATUSES, timestamp),
            )
