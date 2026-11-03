"""Passive, loopback-only capture of DGM-HUB MultiChat history.

The observer performs GET requests only. It never starts providers, posts chat
messages, changes Hub state, or executes provider output.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from core.storage.storage_manager import storage_manager

_SECRET_PATTERNS = (
    re.compile(r"(?i)\b(api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret|password|passwd|cookie|session[_-]?id)\s*[:=]\s*[^\s,;]{6,}"),
    re.compile(r"(?i)\b[A-Z0-9_]*(?:TOKEN|SECRET|API[_-]?KEY|PASSWORD|CREDENTIAL)\s*[:=]\s*[^\s,;]{8,}"),
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{16,}"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bnvapi-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
)
_MAX_EVENTS = 500
_MAX_RESPONSE_BYTES = 4 * 1024 * 1024


class HubObserverError(RuntimeError):
    """The local Hub history could not be captured safely."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _redact(value: Any) -> Any:
    if isinstance(value, str):
        result = value
        for pattern in _SECRET_PATTERNS:
            result = pattern.sub(lambda match: f"{match.group(1)}=[REDACTED]" if match.lastindex else "[REDACTED]", result)
        return result
    if isinstance(value, list):
        return [_redact(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _redact(item) for key, item in value.items()}
    return value


class HubMeetingStore:
    """SQLite event ledger with immutable source fingerprints and idempotent ingest."""

    SCHEMA_VERSION = 1

    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS hub_meeting_events (
                    event_id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    event_kind TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    provider_id TEXT,
                    task_id TEXT,
                    source_sha256 TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    captured_at TEXT NOT NULL,
                    schema_version INTEGER NOT NULL DEFAULT 1
                );
                CREATE INDEX IF NOT EXISTS ix_hub_events_conversation_time
                    ON hub_meeting_events(conversation_id, occurred_at, event_id);
                CREATE INDEX IF NOT EXISTS ix_hub_events_task
                    ON hub_meeting_events(task_id);
                CREATE TABLE IF NOT EXISTS hub_observer_state (
                    state_key TEXT PRIMARY KEY,
                    value_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(str(self.database_path), timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=10000")
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA foreign_keys=ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def event_fingerprint(event: dict[str, Any]) -> str:
        return hashlib.sha256(_canonical_json(event).encode("utf-8")).hexdigest()

    def ingest(self, events: list[Any]) -> dict[str, int | bool]:
        if not isinstance(events, list):
            raise HubObserverError("Hub history did not contain an events array.")
        if len(events) > _MAX_EVENTS:
            raise HubObserverError("Hub history exceeded the requested event window.")
        inserted = duplicates = invalid = 0
        now = _now()
        with self._connection() as db:
            for event in events:
                if not isinstance(event, dict):
                    invalid += 1
                    continue
                conversation_id = event.get("conversation_id")
                occurred_at = event.get("timestamp")
                event_kind = event.get("kind")
                if not all(isinstance(value, str) and value.strip() for value in (conversation_id, occurred_at, event_kind)):
                    invalid += 1
                    continue
                provider_id = event.get("provider") if isinstance(event.get("provider"), str) else None
                task_id = event.get("task_id") if isinstance(event.get("task_id"), str) else None
                if event_kind == "user_message":
                    actor = "operator"
                elif event_kind == "provider_response":
                    actor = provider_id or "unknown_provider"
                elif event_kind == "dgm_mat_observation":
                    actor = "dgm_mat"
                else:
                    actor = provider_id or "unknown"
                source_sha256 = self.event_fingerprint(event)
                safe_payload = _redact(event)
                cursor = db.execute("""
                    INSERT OR IGNORE INTO hub_meeting_events (
                        event_id, conversation_id, occurred_at, event_kind, actor,
                        provider_id, task_id, source_sha256, payload_json, captured_at,
                        schema_version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    source_sha256, conversation_id.strip(), occurred_at.strip(), event_kind.strip(),
                    actor, provider_id, task_id, source_sha256,
                    _canonical_json(safe_payload), now, self.SCHEMA_VERSION,
                ))
                if cursor.rowcount:
                    inserted += 1
                else:
                    duplicates += 1
        result: dict[str, int | bool] = {
            "received": len(events), "inserted": inserted, "duplicates": duplicates,
            "invalid": invalid, "window_saturated": len(events) == _MAX_EVENTS,
        }
        self.set_state("last_capture", {**result, "last_success_at": now, "last_error": None})
        return result

    def set_state(self, key: str, value: dict[str, Any] | None) -> None:
        with self._connection() as db:
            if value is None:
                db.execute("DELETE FROM hub_observer_state WHERE state_key=?", (key,))
                return
            db.execute("""
                INSERT INTO hub_observer_state(state_key, value_json, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(state_key) DO UPDATE SET
                    value_json=excluded.value_json, updated_at=excluded.updated_at
            """, (key, _canonical_json(value), _now()))

    def get_state(self, key: str) -> dict[str, Any] | None:
        with self._connection() as db:
            row = db.execute(
                "SELECT value_json FROM hub_observer_state WHERE state_key=?", (key,)
            ).fetchone()
        return json.loads(row["value_json"]) if row else None

    def status(self) -> dict[str, Any]:
        with self._connection() as db:
            counts = db.execute("""
                SELECT COUNT(*) AS events, COUNT(DISTINCT conversation_id) AS meetings
                FROM hub_meeting_events
            """).fetchone()
        return {
            "storage": "sqlite", "schema_version": self.SCHEMA_VERSION,
            "database_path": str(self.database_path),
            "captured_events": int(counts["events"]),
            "captured_meetings": int(counts["meetings"]),
            "last_capture": self.get_state("last_capture"),
            "last_error": self.get_state("last_error"),
        }

    def list_meetings(self, limit: int = 100) -> list[dict[str, Any]]:
        bounded = max(1, min(int(limit), 500))
        with self._connection() as db:
            rows = db.execute("""
                SELECT conversation_id, MIN(occurred_at) AS first_event_at,
                       MAX(occurred_at) AS last_event_at, COUNT(*) AS event_count,
                       SUM(CASE WHEN event_kind='user_message' THEN 1 ELSE 0 END) AS user_messages,
                       SUM(CASE WHEN event_kind='provider_response' THEN 1 ELSE 0 END) AS provider_responses,
                       SUM(CASE WHEN task_id IS NULL THEN 1 ELSE 0 END) AS events_without_task_id
                FROM hub_meeting_events
                GROUP BY conversation_id
                ORDER BY last_event_at DESC LIMIT ?
            """, (bounded,)).fetchall()
            result = []
            for row in rows:
                participants = db.execute(
                    "SELECT DISTINCT actor FROM hub_meeting_events WHERE conversation_id=? ORDER BY actor",
                    (row["conversation_id"],),
                ).fetchall()
                first_message = db.execute(
                    "SELECT payload_json FROM hub_meeting_events WHERE conversation_id=? AND event_kind='user_message' ORDER BY occurred_at, event_id LIMIT 1",
                    (row["conversation_id"],),
                ).fetchone()
                first_payload = json.loads(first_message["payload_json"]) if first_message else {}
                objective = first_payload.get("message") if isinstance(first_payload.get("message"), str) else ""
                targets = first_payload.get("targets") if isinstance(first_payload.get("targets"), list) else []
                result.append({
                    "conversation_id": row["conversation_id"],
                    "objective": objective[:400],
                    "targets": [str(item)[:80] for item in targets[:20] if isinstance(item, str)],
                    "first_event_at": row["first_event_at"],
                    "last_event_at": row["last_event_at"],
                    "event_count": int(row["event_count"]),
                    "user_messages": int(row["user_messages"] or 0),
                    "provider_responses": int(row["provider_responses"] or 0),
                    "participants": [item["actor"] for item in participants],
                    "task_correlation": (
                        "complete" if int(row["events_without_task_id"] or 0) == 0
                        else "conversation_only_task_id_not_exposed_by_hub"
                    ),
                })
        return result

    def get_meeting(self, conversation_id: str) -> dict[str, Any] | None:
        with self._connection() as db:
            rows = db.execute("""
                SELECT * FROM hub_meeting_events WHERE conversation_id=?
                ORDER BY occurred_at, event_id
            """, (conversation_id,)).fetchall()
        if not rows:
            return None
        events = [{
            "event_id": row["event_id"], "timestamp": row["occurred_at"],
            "kind": row["event_kind"], "actor": row["actor"],
            "provider_id": row["provider_id"], "task_id": row["task_id"],
            "source_sha256": row["source_sha256"],
            "payload": json.loads(row["payload_json"]), "captured_at": row["captured_at"],
        } for row in rows]
        first_user_event = next(
            (item for item in events if item["kind"] == "user_message"), None
        )
        first_payload = first_user_event["payload"] if first_user_event else {}
        objective = first_payload.get("message") if isinstance(first_payload.get("message"), str) else ""
        targets = first_payload.get("targets") if isinstance(first_payload.get("targets"), list) else []
        return {
            "conversation_id": conversation_id,
            "objective": objective[:400],
            "targets": [str(item)[:80] for item in targets[:20] if isinstance(item, str)],
            "participants": sorted({item["actor"] for item in events}),
            "event_count": len(events),
            "task_correlation": (
                "complete" if all(item["task_id"] for item in events)
                else "conversation_only_task_id_not_exposed_by_hub"
            ),
            "events": events,
        }

    def get_event(self, event_id: str) -> dict[str, Any] | None:
        with self._connection() as db:
            row = db.execute(
                "SELECT * FROM hub_meeting_events WHERE event_id=?", (event_id,)
            ).fetchone()
        if not row:
            return None
        return {
            "event_id": row["event_id"], "conversation_id": row["conversation_id"],
            "timestamp": row["occurred_at"], "kind": row["event_kind"],
            "actor": row["actor"], "provider_id": row["provider_id"],
            "task_id": row["task_id"], "payload": json.loads(row["payload_json"]),
        }


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Prevent the loopback observer from following redirects off-device."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class DGMHubMeetingObserver:
    """Bounded polling client for the local read-only history endpoint."""

    def __init__(
        self, store: HubMeetingStore, base_url: str | None = None, *,
        interval_seconds: float = 5.0, request_timeout: float = 4.0,
    ):
        self.store = store
        self.base_url = (base_url or os.getenv(
            "DGM_HUB_MULTICHAT_URL", "http://127.0.0.1:8770"
        )).rstrip("/")
        self.interval_seconds = max(1.0, min(float(interval_seconds), 30.0))
        self.request_timeout = max(1.0, min(float(request_timeout), 10.0))
        self._validate_url()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.RLock()

    def _validate_url(self) -> None:
        parsed = urllib.parse.urlsplit(self.base_url)
        try:
            port = parsed.port
        except ValueError as exc:
            raise HubObserverError("DGM-HUB URL contains an invalid port.") from exc
        if (
            parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "::1"}
            or port != 8770 or parsed.username is not None or parsed.password is not None
            or parsed.path not in {"", "/"} or parsed.query or parsed.fragment
        ):
            raise HubObserverError("Meeting observer only permits HTTP loopback on port 8770.")

    def capture_once(self) -> dict[str, Any]:
        request = urllib.request.Request(
            self.base_url + "/api/history?limit=500",
            headers={"Accept": "application/json"}, method="GET",
        )
        try:
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirectHandler())
            with opener.open(request, timeout=self.request_timeout) as response:
                if response.status != 200:
                    raise HubObserverError(f"Hub history returned HTTP {response.status}.")
                raw = response.read(_MAX_RESPONSE_BYTES + 1)
        except urllib.error.HTTPError as exc:
            raise HubObserverError(f"Hub history returned HTTP {exc.code}.") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            message = f"Hub history is unavailable ({type(exc).__name__})."
            self.store.set_state("last_error", {"message": message, "at": _now()})
            raise HubObserverError(message) from exc
        if len(raw) > _MAX_RESPONSE_BYTES:
            raise HubObserverError("Hub history response exceeded the 4 MiB safety limit.")
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise HubObserverError("Hub history returned invalid JSON.") from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("events"), list):
            raise HubObserverError("Hub history returned an unexpected response shape.")
        result = self.store.ingest(payload["events"])
        result["hub"] = "online"
        result["capture_mode"] = "read_only_poll"
        if result["window_saturated"]:
            result["warning"] = "Hub returned the full 500-event window; older unseen events may be missing."
        self.store.set_state("last_error", None)
        return result

    def start(self) -> bool:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return False
            self._stop.clear()
            self._thread = threading.Thread(
                target=self._run, name="dgm-hub-meeting-observer", daemon=True
            )
            self._thread.start()
            return True

    def stop(self, timeout: float = 5.0) -> None:
        self._stop.set()
        thread = self._thread
        if thread and thread.is_alive():
            thread.join(max(0.1, min(float(timeout), 5.0)))

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                self.capture_once()
            except HubObserverError as exc:
                self.store.set_state("last_error", {"message": str(exc), "at": _now()})
            self._stop.wait(self.interval_seconds)

    def runtime_status(self) -> dict[str, Any]:
        thread = self._thread
        return {
            **self.store.status(),
            "observer_running": bool(thread and thread.is_alive()),
            "capture_mode": "read_only_poll", "hub_endpoint": self.base_url,
            "provider_calls": 0, "messages_sent": 0,
            "task_id_source_field": "Hub history does not currently expose task_id on journal events.",
        }


_observer: DGMHubMeetingObserver | None = None
_observer_lock = threading.Lock()


def get_hub_meeting_observer() -> DGMHubMeetingObserver:
    global _observer
    with _observer_lock:
        if _observer is None:
            database = storage_manager.get_path("tasks") / "hub_meeting_observer.sqlite3"
            _observer = DGMHubMeetingObserver(HubMeetingStore(database))
        return _observer