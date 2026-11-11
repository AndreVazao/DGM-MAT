"""Local in-process control signal for an orderly DGM-MAT runtime shutdown."""
from __future__ import annotations

from threading import Event

_shutdown_requested = Event()


def reset_runtime_shutdown_request() -> None:
    """Clear the shutdown request before a fresh runtime starts."""
    _shutdown_requested.clear()


def request_runtime_shutdown() -> None:
    """Request shutdown; the runtime owner performs the actual cleanup."""
    _shutdown_requested.set()


def wait_for_runtime_shutdown(timeout: float = 1.0) -> bool:
    """Wait for an operator shutdown request without busy-spinning."""
    return _shutdown_requested.wait(max(0.0, float(timeout)))


def runtime_shutdown_is_requested() -> bool:
    return _shutdown_requested.is_set()
