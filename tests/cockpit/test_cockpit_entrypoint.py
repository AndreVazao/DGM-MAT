import sys

import pytest

import main as dgm_main


def test_cockpit_only_starts_client_without_starting_runtime(monkeypatch):
    cockpit_calls = []

    monkeypatch.setattr(sys, "argv", ["main.py", "--cockpit-only"])
    monkeypatch.setattr("cockpit.app.run_cockpit", lambda: cockpit_calls.append("started"))
    monkeypatch.setattr(
        dgm_main,
        "run_runtime",
        lambda **_kwargs: pytest.fail("cockpit-only must not start a backend runtime"),
    )

    dgm_main.main()

    assert cockpit_calls == ["started"]


def test_headless_and_cockpit_only_are_rejected_together(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["main.py", "--headless", "--cockpit-only"])

    with pytest.raises(SystemExit) as exc:
        dgm_main.main()

    assert exc.value.code == 2
