"""Bounded background verification of GitHub repository references.

Only public repository metadata is queried. No GitHub credentials, provider sessions,
conversation bodies, or source archives are sent to GitHub.
"""
from __future__ import annotations

import logging
import os
import threading
from typing import Any, Callable

_LOG = logging.getLogger(__name__)

ENABLED_ENV = "DGM_GITHUB_REFERENCE_VERIFIER_ENABLED"
INTERVAL_ENV = "DGM_GITHUB_REFERENCE_VERIFIER_INTERVAL_SECONDS"
BATCH_ENV = "DGM_GITHUB_REFERENCE_VERIFIER_BATCH_SIZE"
DEFAULT_INTERVAL_SECONDS = 30 * 60
DEFAULT_BATCH_SIZE = 5
MAX_BATCH_SIZE = 10


def _bounded_int(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(value, maximum))


def verifier_enabled() -> bool:
    """Enabled by default; operators can disable all outbound GitHub checks explicitly."""
    return os.getenv(ENABLED_ENV, "1").strip().casefold() not in {
        "0", "false", "no", "off", "disabled",
    }


def verifier_interval_seconds() -> int:
    """Run at most twice per hour by default; never poll more frequently than 5 minutes."""
    return _bounded_int(INTERVAL_ENV, DEFAULT_INTERVAL_SECONDS, 5 * 60, 24 * 60 * 60)


def verifier_batch_size() -> int:
    """Keep unauthenticated GitHub API usage small and bounded."""
    return _bounded_int(BATCH_ENV, DEFAULT_BATCH_SIZE, 1, MAX_BATCH_SIZE)


def verify_pending_references(*, limit: int) -> dict[str, Any]:
    """Verify a bounded number of pending references using the existing public-only verifier."""
    from core.vault import VaultCatalog

    configured = os.getenv("DGM_VAULT_PATH") or VaultCatalog.default_root()
    return VaultCatalog(configured).verify_pending_github_repository_references(
        limit=limit,
        timeout=5.0,
    )


class GitHubReferenceVerifierWorker:
    """Single-process daemon worker with a startup delay, cooldown and clean shutdown."""

    def __init__(
        self,
        verifier: Callable[..., dict[str, Any]] | None = None,
        *,
        initial_delay_seconds: int = 15,
    ) -> None:
        self._verifier = verifier or verify_pending_references
        self._initial_delay_seconds = max(0, min(int(initial_delay_seconds), 300))
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def start(self) -> bool:
        if not verifier_enabled():
            _LOG.info("GitHub reference verifier disabled by %s", ENABLED_ENV)
            return False
        with self._lock:
            if self.is_running:
                return True
            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._run,
                name="dgm-github-reference-verifier",
                daemon=True,
            )
            self._thread.start()
        _LOG.info(
            "GitHub reference verifier started: batch=%s interval=%ss; public unauthenticated metadata only",
            verifier_batch_size(),
            verifier_interval_seconds(),
        )
        return True

    def stop(self, timeout: float = 2.0) -> None:
        self._stop_event.set()
        thread = self._thread
        if thread and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=max(0.0, min(float(timeout), 5.0)))

    def run_once(self) -> dict[str, Any]:
        """Expose one bounded cycle for deterministic tests and operator diagnostics."""
        result = self._verifier(limit=verifier_batch_size())
        if not isinstance(result, dict):
            raise TypeError("GitHub reference verifier must return a dictionary")
        return result

    def _run(self) -> None:
        if self._stop_event.wait(self._initial_delay_seconds):
            return
        while not self._stop_event.is_set():
            try:
                result = self.run_once()
                _LOG.info(
                    "GitHub reference verification cycle completed: checked=%s",
                    result.get("checked", 0),
                )
            except Exception:
                _LOG.exception("GitHub reference verification cycle failed; next bounded retry remains scheduled")
            if self._stop_event.wait(verifier_interval_seconds()):
                return
