# Path: C:\\ProgramasGodMode\\DGM-MAT\\core\\api\\local_sessions.py
"""In-memory, short-lived local API sessions for staged client migration.

This module deliberately does not issue sessions over HTTP and is not wired
into the API yet. A caller must authenticate the bootstrap/pairing ceremony
before calling create_session(). Tokens are returned once; only SHA-256
digests are retained. Restarting the process invalidates all sessions.
"""
from __future__ import annotations

import hashlib
import secrets
import threading
import time
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class LocalPrincipal:
    subject: str
    scopes: frozenset[str]
    issued_at: float
    expires_at: float
    session_id: str


@dataclass(frozen=True)
class _SessionRecord:
    subject: str
    scopes: frozenset[str]
    issued_at: float
    expires_at: float
    session_id: str


class LocalSessionManager:
    """Thread-safe bearer session manager with TTL, scope checks and revocation."""

    def __init__(self, *, ttl_seconds: int = 1800, clock=time.time):
        if not isinstance(ttl_seconds, int) or isinstance(ttl_seconds, bool) or not 60 <= ttl_seconds <= 86400:
            raise ValueError("ttl_seconds must be between 60 and 86400")
        self._ttl_seconds = ttl_seconds
        self._clock = clock
        self._records: dict[bytes, _SessionRecord] = {}
        self._lock = threading.RLock()

    @staticmethod
    def _digest(token: str) -> bytes:
        return hashlib.sha256(token.encode("utf-8")).digest()

    def create_session(self, subject: str, scopes: Iterable[str]) -> tuple[str, LocalPrincipal]:
        if not isinstance(subject, str) or not subject.strip() or len(subject) > 128:
            raise ValueError("subject must be a non-empty string of at most 128 characters")
        normalized = frozenset(
            scope for scope in scopes
            if isinstance(scope, str) and scope and len(scope) <= 64
        )
        if not normalized:
            raise ValueError("at least one valid scope is required")
        now = self._clock()
        token = secrets.token_urlsafe(32)
        session_id = secrets.token_hex(16)
        record = _SessionRecord(subject.strip(), normalized, now, now + self._ttl_seconds, session_id)
        with self._lock:
            self._purge_expired_locked(now)
            self._records[self._digest(token)] = record
        return token, LocalPrincipal(record.subject, record.scopes, record.issued_at, record.expires_at, record.session_id)

    def authenticate(self, token: str | None, *, required_scope: str | None = None) -> LocalPrincipal | None:
        if not isinstance(token, str) or not token or len(token) > 512:
            return None
        digest = self._digest(token)
        now = self._clock()
        with self._lock:
            self._purge_expired_locked(now)
            record = self._records.get(digest)
            if record is None or (required_scope is not None and required_scope not in record.scopes):
                return None
            return LocalPrincipal(record.subject, record.scopes, record.issued_at, record.expires_at, record.session_id)

    def revoke(self, token: str | None) -> bool:
        if not isinstance(token, str) or not token or len(token) > 512:
            return False
        with self._lock:
            return self._records.pop(self._digest(token), None) is not None

    def revoke_all(self) -> int:
        with self._lock:
            count = len(self._records)
            self._records.clear()
            return count

    def active_count(self) -> int:
        now = self._clock()
        with self._lock:
            self._purge_expired_locked(now)
            return len(self._records)

    def _purge_expired_locked(self, now: float) -> None:
        expired = [digest for digest, record in self._records.items() if record.expires_at <= now]
        for digest in expired:
            self._records.pop(digest, None)
