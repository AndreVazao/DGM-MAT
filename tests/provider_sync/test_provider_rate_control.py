# Path: C:\\ProgramasGodMode\\DGM-MAT\\tests\\provider_sync\\test_provider_rate_control.py

import threading

import pytest

from core.governance import provider_rate_control
from core.governance.provider_rate_control import ProviderRateControl


@pytest.mark.parametrize("value", [0, -1, True, False, 1.5, "10", None])
def test_rate_control_rejects_invalid_limits(value):
    with pytest.raises(ValueError, match="positive integer"):
        ProviderRateControl(value)


@pytest.mark.parametrize("provider_id", ["", "  ", None, 12])
def test_rate_control_rejects_invalid_provider_ids(provider_id):
    limiter = ProviderRateControl(2)
    assert limiter.allow_request(provider_id) is False


def test_rate_control_enforces_per_provider_sliding_window(monkeypatch):
    clock = {"now": 100.0}
    monkeypatch.setattr(provider_rate_control.time, "monotonic", lambda: clock["now"])
    limiter = ProviderRateControl(2)

    assert limiter.allow_request("provider-a") is True
    assert limiter.allow_request("provider-a") is True
    assert limiter.allow_request("provider-a") is False
    assert limiter.allow_request("provider-b") is True

    clock["now"] = 160.001
    assert limiter.allow_request("provider-a") is True


def test_rate_control_is_thread_safe_under_competing_requests(monkeypatch):
    monkeypatch.setattr(provider_rate_control.time, "monotonic", lambda: 100.0)
    limiter = ProviderRateControl(5)
    barrier = threading.Barrier(20)
    results = []
    result_lock = threading.Lock()

    def attempt():
        barrier.wait()
        result = limiter.allow_request("provider-a")
        with result_lock:
            results.append(result)

    threads = [threading.Thread(target=attempt) for _ in range(20)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=2)

    assert all(not thread.is_alive() for thread in threads)
    assert sum(results) == 5
    assert len(limiter.request_counts["provider-a"]) == 5


def test_rate_control_normalizes_provider_id():
    limiter = ProviderRateControl(1)
    assert limiter.allow_request(" provider-a ") is True
    assert limiter.allow_request("provider-a") is False
