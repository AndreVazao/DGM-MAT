from types import SimpleNamespace

from core.self_healing.self_repair_engine import SelfRepairEngine


def _audit(*, readme_present: bool):
    return SimpleNamespace(
        name="example",
        origin="https://github.com/example/example.git",
        dirty=False,
        readme_present=readme_present,
    )


def _automatic_action():
    return {
        "id": "SELF-001",
        "category": "self-test",
        "risk": "LOW",
        "description": "Run bounded runtime validation.",
        "allowed_automatically": True,
        "command": None,
    }


def test_plan_requires_approval_to_repair_missing_readme(tmp_path):
    engine = SelfRepairEngine(tmp_path / "example")

    actions = engine._plan(_audit(readme_present=False))

    readme_actions = [action for action in actions if action.id == "README-001"]
    assert len(readme_actions) == 1
    assert readme_actions[0].allowed_automatically is False


def test_plan_does_not_propose_readme_repair_when_readme_exists(tmp_path):
    engine = SelfRepairEngine(tmp_path / "example")

    actions = engine._plan(_audit(readme_present=True))

    assert all(action.id != "README-001" for action in actions)


def test_apply_safe_reports_dry_run_actions_as_planned_not_applied(tmp_path, monkeypatch):
    engine = SelfRepairEngine(tmp_path / "example")
    action = _automatic_action()
    monkeypatch.setattr(engine, "diagnose", lambda: {"actions": [action]})

    def unexpected_execution(_action):
        raise AssertionError("Dry-run must not execute actions")

    monkeypatch.setattr(engine, "_run_safe_action", unexpected_execution)

    result = engine.apply_safe(dry_run=True)

    assert result["planned"] == [{**action, "status": "planned"}]
    assert result["applied"] == []
    assert result["failed"] == []


def test_apply_safe_reports_failed_actions_separately(tmp_path, monkeypatch):
    engine = SelfRepairEngine(tmp_path / "example")
    action = _automatic_action()
    monkeypatch.setattr(engine, "diagnose", lambda: {"actions": [action]})
    monkeypatch.setattr(
        engine,
        "_run_safe_action",
        lambda _action: {"status": "failed", "returncode": 1},
    )

    result = engine.apply_safe(dry_run=False)

    assert result["applied"] == []
    assert result["failed"] == [{**action, "status": "failed", "returncode": 1}]


def test_apply_safe_only_lists_successful_actions_as_applied(tmp_path, monkeypatch):
    engine = SelfRepairEngine(tmp_path / "example")
    action = _automatic_action()
    monkeypatch.setattr(engine, "diagnose", lambda: {"actions": [action]})
    monkeypatch.setattr(
        engine,
        "_run_safe_action",
        lambda _action: {"status": "passed", "returncode": 0},
    )

    result = engine.apply_safe(dry_run=False)

    assert result["applied"] == [{**action, "status": "passed", "returncode": 0}]
    assert result["planned"] == []
    assert result["failed"] == []
