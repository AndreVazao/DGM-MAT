from __future__ import annotations

from core.runtime.runtime import repository_learning_autostart_enabled


def test_repository_learning_autostart_defaults_to_enabled(monkeypatch):
    monkeypatch.delenv("DGM_REPOSITORY_LEARNING_ENABLED", raising=False)
    assert repository_learning_autostart_enabled() is True


def test_repository_learning_autostart_can_be_explicitly_disabled(monkeypatch):
    monkeypatch.setenv("DGM_REPOSITORY_LEARNING_ENABLED", "0")
    assert repository_learning_autostart_enabled() is False


def test_repository_learning_autostart_accepts_explicit_true_values():
    for value in ("1", "true", "YES", " on "):
        assert repository_learning_autostart_enabled(value) is True


def test_repository_learning_autostart_rejects_other_values():
    for value in ("", "false", "off", "disabled", "2"):
        assert repository_learning_autostart_enabled(value) is False
