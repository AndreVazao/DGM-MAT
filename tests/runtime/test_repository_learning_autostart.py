from __future__ import annotations

from core.runtime.runtime import repository_learning_autostart_enabled


def test_repository_learning_autostart_defaults_to_enabled_on_standard_profile(monkeypatch):
    monkeypatch.delenv("DGM_REPOSITORY_LEARNING_ENABLED", raising=False)
    assert repository_learning_autostart_enabled(low_memory=False) is True


def test_repository_learning_autostart_defaults_to_disabled_on_low_memory_profile(monkeypatch):
    monkeypatch.delenv("DGM_REPOSITORY_LEARNING_ENABLED", raising=False)
    assert repository_learning_autostart_enabled(low_memory=True) is False


def test_explicit_opt_in_overrides_low_memory_profile(monkeypatch):
    monkeypatch.setenv("DGM_REPOSITORY_LEARNING_ENABLED", "1")
    assert repository_learning_autostart_enabled(low_memory=True) is True


def test_repository_learning_autostart_can_be_explicitly_disabled(monkeypatch):
    monkeypatch.setenv("DGM_REPOSITORY_LEARNING_ENABLED", "0")
    assert repository_learning_autostart_enabled(low_memory=False) is False


def test_repository_learning_autostart_accepts_explicit_true_values():
    for value in ("1", "true", "YES", " on "):
        assert repository_learning_autostart_enabled(value, low_memory=True) is True


def test_repository_learning_autostart_rejects_other_values():
    for value in ("", "false", "off", "disabled", "2"):
        assert repository_learning_autostart_enabled(value, low_memory=False) is False
