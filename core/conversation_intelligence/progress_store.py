from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .models import ConversationRecord


class ConversationProgressStore:
    """Durable, idempotent ledger so completed history is not repeatedly reprocessed."""

    SCHEMA_VERSION = 1

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS conversation_progress (
                    provider TEXT NOT NULL,
                    conversation_id TEXT NOT NULL,
                    source_fingerprint TEXT NOT NULL,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('discovered','processing','complete','needs_review','failed')),
                    processed_at TEXT,
                    last_error TEXT,
                    result_json TEXT,
                    schema_version INTEGER NOT NULL DEFAULT 1,
                    PRIMARY KEY (provider, conversation_id)
                );
                CREATE TABLE IF NOT EXISTS source_progress (
                    provider TEXT NOT NULL,
                    source_key TEXT NOT NULL,
                    source_fingerprint TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('partial','complete','blocked_login','rate_limited','failed','needs_user')),
                    discovered_count INTEGER NOT NULL DEFAULT 0,
                    imported_count INTEGER NOT NULL DEFAULT 0,
                    checkpoint TEXT,
                    updated_at TEXT NOT NULL,
                    last_error TEXT,
                    PRIMARY KEY (provider, source_key)
                );
            """)

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(str(self.database_path), timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA foreign_keys=ON")
        return db

    @staticmethod
    def fingerprint(value: str | bytes) -> str:
        raw = value.encode("utf-8") if isinstance(value, str) else value
        return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def should_process(self, provider: str, conversation_id: str, source_fingerprint: str) -> bool:
        with self._connect() as db:
            row = db.execute(
                "SELECT source_fingerprint, status FROM conversation_progress WHERE provider=? AND conversation_id=?",
                (provider, conversation_id),
            ).fetchone()
        return row is None or row["source_fingerprint"] != source_fingerprint or row["status"] != "complete"

    def record_conversation(
        self,
        provider: str,
        conversation_id: str,
        source_fingerprint: str,
        title: str,
        status: str = "complete",
        result: dict | None = None,
        last_error: str | None = None,
    ) -> None:
        if status not in {"discovered", "processing", "complete", "needs_review", "failed"}:
            raise ValueError(f"Unsupported conversation status: {status}")
        if status == "complete" and last_error:
            raise ValueError("A completed conversation cannot retain a last_error")
        with self._connect() as db:
            db.execute("""
                INSERT INTO conversation_progress
                    (provider, conversation_id, source_fingerprint, title, status, processed_at, last_error, result_json, schema_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(provider, conversation_id) DO UPDATE SET
                    source_fingerprint=excluded.source_fingerprint,
                    title=excluded.title,
                    status=excluded.status,
                    processed_at=excluded.processed_at,
                    last_error=excluded.last_error,
                    result_json=excluded.result_json,
                    schema_version=excluded.schema_version
            """, (
                provider, conversation_id, source_fingerprint, title, status,
                self._now() if status == "complete" else None,
                last_error,
                json.dumps(result, ensure_ascii=False, sort_keys=True) if result is not None else None,
                self.SCHEMA_VERSION,
            ))

    def record_source(
        self,
        provider: str,
        source_key: str,
        source_fingerprint: str,
        status: str,
        discovered_count: int,
        imported_count: int,
        checkpoint: str | None = None,
        last_error: str | None = None,
    ) -> None:
        allowed = {"partial", "complete", "blocked_login", "rate_limited", "failed", "needs_user"}
        if status not in allowed:
            raise ValueError(f"Unsupported source status: {status}")
        if discovered_count < 0 or imported_count < 0 or imported_count > discovered_count:
            raise ValueError("Source counts must satisfy 0 <= imported_count <= discovered_count")
        if status == "complete" and imported_count != discovered_count:
            raise ValueError("Complete source status requires all discovered items to be imported")
        with self._connect() as db:
            db.execute("""
                INSERT INTO source_progress
                    (provider, source_key, source_fingerprint, status, discovered_count, imported_count, checkpoint, updated_at, last_error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(provider, source_key) DO UPDATE SET
                    source_fingerprint=excluded.source_fingerprint,
                    status=excluded.status,
                    discovered_count=excluded.discovered_count,
                    imported_count=excluded.imported_count,
                    checkpoint=excluded.checkpoint,
                    updated_at=excluded.updated_at,
                    last_error=excluded.last_error
            """, (
                provider, source_key, source_fingerprint, status, discovered_count,
                imported_count, checkpoint, self._now(), last_error,
            ))

    def get_source(self, provider: str, source_key: str) -> dict | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT * FROM source_progress WHERE provider=? AND source_key=?",
                (provider, source_key),
            ).fetchone()
        return dict(row) if row else None

    def pending_conversations(self, provider: str | None = None) -> list[dict]:
        query = "SELECT * FROM conversation_progress WHERE status != 'complete'"
        params: tuple = ()
        if provider is not None:
            query += " AND provider=?"
            params = (provider,)
        query += " ORDER BY provider, conversation_id"
        with self._connect() as db:
            return [dict(row) for row in db.execute(query, params).fetchall()]

    def summary(self) -> dict[str, int]:
        with self._connect() as db:
            rows = db.execute("SELECT status, COUNT(*) AS count FROM conversation_progress GROUP BY status").fetchall()
            source_rows = db.execute("SELECT status, COUNT(*) AS count FROM source_progress GROUP BY status").fetchall()
        return {
            **{f"conversations_{row['status']}": row["count"] for row in rows},
            **{f"sources_{row['status']}": row["count"] for row in source_rows},
        }
