from __future__ import annotations

from core.vault.github_reference_verifier import (
    BATCH_ENV,
    ENABLED_ENV,
    INTERVAL_ENV,
    GitHubReferenceVerifierWorker,
    verifier_batch_size,
    verifier_enabled,
    verifier_interval_seconds,
)


def test_verifier_is_enabled_by_default_but_can_be_disabled(monkeypatch):
    monkeypatch.delenv(ENABLED_ENV, raising=False)
    assert verifier_enabled() is True
    monkeypatch.setenv(ENABLED_ENV, "0")
    assert verifier_enabled() is False
    monkeypatch.setenv(ENABLED_ENV, "false")
    assert verifier_enabled() is False


def test_verifier_interval_is_bounded(monkeypatch):
    monkeypatch.delenv(INTERVAL_ENV, raising=False)
    assert verifier_interval_seconds() == 1800
    monkeypatch.setenv(INTERVAL_ENV, "1")
    assert verifier_interval_seconds() == 300
    monkeypatch.setenv(INTERVAL_ENV, "999999")
    assert verifier_interval_seconds() == 86400
    monkeypatch.setenv(INTERVAL_ENV, "invalid")
    assert verifier_interval_seconds() == 1800


def test_verifier_batch_is_bounded(monkeypatch):
    monkeypatch.delenv(BATCH_ENV, raising=False)
    assert verifier_batch_size() == 5
    monkeypatch.setenv(BATCH_ENV, "0")
    assert verifier_batch_size() == 1
    monkeypatch.setenv(BATCH_ENV, "500")
    assert verifier_batch_size() == 10


def test_worker_runs_one_bounded_cycle(monkeypatch):
    monkeypatch.setenv(BATCH_ENV, "3")
    seen = {}

    def fake_verifier(*, limit):
        seen["limit"] = limit
        return {"checked": 2, "results": []}

    worker = GitHubReferenceVerifierWorker(fake_verifier, initial_delay_seconds=0)
    result = worker.run_once()

    assert seen["limit"] == 3
    assert result["checked"] == 2


def test_disabled_worker_does_not_start(monkeypatch):
    monkeypatch.setenv(ENABLED_ENV, "off")
    worker = GitHubReferenceVerifierWorker(lambda **_: {"checked": 0})
    assert worker.start() is False
    assert worker.is_running is False
