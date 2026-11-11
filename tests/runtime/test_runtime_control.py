from __future__ import annotations

from core.runtime.runtime_control import (
    request_runtime_shutdown,
    reset_runtime_shutdown_request,
    runtime_shutdown_is_requested,
    wait_for_runtime_shutdown,
)


def test_runtime_shutdown_request_is_event_driven_and_resettable():
    reset_runtime_shutdown_request()
    assert runtime_shutdown_is_requested() is False
    assert wait_for_runtime_shutdown(0.001) is False

    request_runtime_shutdown()
    assert runtime_shutdown_is_requested() is True
    assert wait_for_runtime_shutdown(0.001) is True

    reset_runtime_shutdown_request()
    assert runtime_shutdown_is_requested() is False
