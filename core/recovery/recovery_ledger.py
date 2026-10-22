"""Durable, forward-only ledger for recovery-first conversation/artifact ingestion.

This module records provenance and progress only. It does not access providers,
delete source conversations, or claim that an archive is complete without evidence.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class RecoveryLedgerError(RuntimeError):
    """Base error for invalid recovery-ledger operations."""


@dataclass(frozen=True)
class RecoverySource:
    provider: str
    source_id: str
    title: str
    source_date: str
    source_url: str = ""
    original_location: str = ""
    project_key: str = ""
    capture_status: str = "discovered"
    raw_archive_path: str = ""
    raw_sha256: str = ""
    completeness: str = "unknown"
    index_status: str = "pending"
    repo_status: str = "pending"
    tree_revision: str = ""
    deletion_status: str = "not_eligible"
    last_error: str = ""
    attempts: int = 0


class RecoveryLedger:
    """Small SQLite registry with idempotent sources and a durable forward cursor."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path).expanduser().resolve()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(str(self.database_path), timeout=5.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 5000")
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as db:
            db.execute("PRAGMA journal_mode = WAL")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS recovery_sources (
                    provider TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    source_date TEXT NOT NULL,
                    source_url TEXT NOT NULL DEFAULT '',
                    original_location TEXT NOT NULL DEFAULT '',
                    project_key TEXT NOT NULL DEFAULT '',
                    capture_status TEXT NOT NULL DEFAULT 'discovered',
                    raw_archive_path TEXT NOT NULL DEFAULT '',
                    raw_sha256 TEXT NOT NULL DEFAULT '',
                    completeness TEXT NOT NULL DEFAULT 'unknown',
                    index_status TEXT NOT NULL DEFAULT 'pending',
                    repo_status TEXT NOT NULL DEFAULT 'pending',
                    tree_revision TEXT NOT NULL DEFAULT '',
                    deletion_status TEXT NOT NULL DEFAULT 'not_eligible',
                    last_error TEXT NOT NULL DEFAULT '',
                    attempts INTEGER NOT NULL DEFAULT 0,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    PRIMARY KEY (provider, source_id)
                );
                CREATE INDEX IF NOT EXISTS idx_recovery_sources_order
                    ON recovery_sources(provider, source_date, source_id);
                CREATE TABLE IF NOT EXISTS recovery_cursor (
                    pipeline TEXT PRIMARY KEY,
                    last_provider TEXT NOT NULL DEFAULT '',
                    last_source_date TEXT NOT NULL DEFAULT '',
                    last_source_id TEXT NOT NULL DEFAULT '',
                    updated_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS recovery_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    event TEXT NOT NULL,
                    detail TEXT NOT NULL DEFAULT '',
                    occurred_at REAL NOT NULL
                );
            """)

    def register(self, source: RecoverySource) -> None:
        if not source.provider.strip() or not source.source_id.strip():
            raise ValueError("provider and source_id must be non-empty.")
        if not source.title.strip() or not source.source_date.strip():
            raise ValueError("title and source_date must be non-empty.")
        now = time.time()
        with self._connect() as db:
            db.execute("""
                INSERT INTO recovery_sources (
                    provider, source_id, title, source_date, source_url,
                    original_location, project_key, capture_status, raw_archive_path,
                    raw_sha256, completeness, index_status, repo_status, tree_revision,
                    deletion_status, last_error, attempts, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(provider, source_id) DO UPDATE SET
                    title=excluded.title, source_date=excluded.source_date,
                    source_url=excluded.source_url,
                    original_location=excluded.original_location,
                    project_key=excluded.project_key, updated_at=excluded.updated_at
            """, (
                source.provider, source.source_id, source.title, source.source_date,
                source.source_url, source.original_location, source.project_key,
                source.capture_status, source.raw_archive_path, source.raw_sha256,
                source.completeness, source.index_status, source.repo_status,
                source.tree_revision, source.deletion_status, source.last_error,
                source.attempts, now, now,
            ))

    def next_source(self, pipeline: str = "conversation_recovery") -> RecoverySource | None:
        """Return the earliest unfinished source after the cursor and record an attempt."""
        with self._connect() as db:
            cursor = db.execute(
                "SELECT * FROM recovery_cursor WHERE pipeline=?", (pipeline,)
            ).fetchone()
            if cursor:
                row = db.execute("""
                    SELECT * FROM recovery_sources
                    WHERE (provider, source_date, source_id) > (?, ?, ?)
                      AND capture_status NOT IN ('verified', 'captured')
                    ORDER BY provider, source_date, source_id LIMIT 1
                """, (cursor["last_provider"], cursor["last_source_date"],
                      cursor["last_source_id"])).fetchone()
            else:
                row = db.execute("""
                    SELECT * FROM recovery_sources
                    WHERE capture_status NOT IN ('verified', 'captured')
                    ORDER BY provider, source_date, source_id LIMIT 1
                """).fetchone()
            if row is None:
                return None
            now = time.time()
            db.execute("""
                UPDATE recovery_sources
                SET capture_status='in_progress', attempts=attempts+1,
                    last_error='', updated_at=?
                WHERE provider=? AND source_id=?
            """, (now, row["provider"], row["source_id"]))
            db.execute("""
                INSERT INTO recovery_events(provider, source_id, event, detail, occurred_at)
                VALUES (?, ?, 'claimed', ?, ?)
            """, (row["provider"], row["source_id"], pipeline, now))
            values = dict(row)
            values["capture_status"] = "in_progress"
            values["attempts"] = row["attempts"] + 1
            values["last_error"] = ""
            return RecoverySource(**{
                key: values[key] for key in RecoverySource.__dataclass_fields__
            })

    def checkpoint(
        self,
        provider: str,
        source_id: str,
        *,
        capture_status: str,
        completeness: str = "unknown",
        raw_archive_path: str = "",
        raw_sha256: str = "",
        index_status: str = "pending",
        repo_status: str = "pending",
        tree_revision: str = "",
        detail: str = "",
        pipeline: str = "conversation_recovery",
    ) -> None:
        """Persist progress; only captured/verified advances the cursor.

        Failures and partial captures remain retryable. No deletion is performed here.
        """
        allowed = {"discovered", "in_progress", "partial", "captured", "verified", "blocked", "failed"}
        if capture_status not in allowed:
            raise ValueError(f"unsupported capture_status: {capture_status}")
        if raw_sha256 and (
            len(raw_sha256) != 64 or any(c not in "0123456789abcdefABCDEF" for c in raw_sha256)
        ):
            raise ValueError("raw_sha256 must be a full SHA-256 hex digest.")
        if capture_status == "verified" and (not raw_archive_path or not raw_sha256):
            raise RecoveryLedgerError("verified capture requires archive path and SHA-256.")
        now = time.time()
        with self._connect() as db:
            row = db.execute(
                "SELECT provider, source_id, source_date FROM recovery_sources WHERE provider=? AND source_id=?",
                (provider, source_id),
            ).fetchone()
            if row is None:
                raise RecoveryLedgerError("cannot checkpoint an unregistered source.")
            db.execute("""
                UPDATE recovery_sources SET capture_status=?, completeness=?,
                    raw_archive_path=?, raw_sha256=?, index_status=?, repo_status=?,
                    tree_revision=?, last_error=?, updated_at=?
                WHERE provider=? AND source_id=?
            """, (
                capture_status, completeness, raw_archive_path, raw_sha256,
                index_status, repo_status, tree_revision,
                detail if capture_status in {"blocked", "failed", "partial"} else "",
                now, provider, source_id,
            ))
            db.execute("""
                INSERT INTO recovery_events(provider, source_id, event, detail, occurred_at)
                VALUES (?, ?, ?, ?, ?)
            """, (provider, source_id, capture_status, detail, now))
            # Advance only across a contiguous completed prefix. A later source
            # checkpointed out of order must never cause earlier work to be skipped.
            cursor = db.execute(
                "SELECT * FROM recovery_cursor WHERE pipeline=?", (pipeline,)
            ).fetchone()
            if cursor:
                completed = db.execute("""
                    SELECT provider, source_date, source_id, capture_status
                    FROM recovery_sources
                    WHERE (provider, source_date, source_id) >
                        (?, ?, ?)
                    ORDER BY provider, source_date, source_id
                """, (cursor["last_provider"], cursor["last_source_date"],
                      cursor["last_source_id"])).fetchall()
                last = (cursor["last_provider"], cursor["last_source_date"],
                        cursor["last_source_id"])
            else:
                completed = db.execute("""
                    SELECT provider, source_date, source_id, capture_status
                    FROM recovery_sources
                    ORDER BY provider, source_date, source_id
                """).fetchall()
                last = None
            for item in completed:
                if item["capture_status"] not in {"captured", "verified"}:
                    break
                last = (item["provider"], item["source_date"], item["source_id"])
            if last is not None and (cursor is None or last != (
                cursor["last_provider"], cursor["last_source_date"], cursor["last_source_id"]
            )):
                db.execute("""
                    INSERT INTO recovery_cursor(
                        pipeline, last_provider, last_source_date, last_source_id, updated_at
                    ) VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(pipeline) DO UPDATE SET
                        last_provider=excluded.last_provider,
                        last_source_date=excluded.last_source_date,
                        last_source_id=excluded.last_source_id,
                        updated_at=excluded.updated_at
                """, (pipeline, *last, now))

    def get(self, provider: str, source_id: str) -> RecoverySource | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT * FROM recovery_sources WHERE provider=? AND source_id=?",
                (provider, source_id),
            ).fetchone()
        return RecoverySource(**{key: row[key] for key in RecoverySource.__dataclass_fields__}) if row else None

    def list_sources(self) -> list[RecoverySource]:
        with self._connect() as db:
            rows = db.execute("""
                SELECT * FROM recovery_sources
                ORDER BY provider, source_date, source_id
            """).fetchall()
        return [RecoverySource(**{key: row[key] for key in RecoverySource.__dataclass_fields__}) for row in rows]

    @staticmethod
    def sha256_file(path: str | Path) -> str:
        """Hash an existing local archive file; does not assert completeness."""
        digest = hashlib.sha256()
        with Path(path).open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
