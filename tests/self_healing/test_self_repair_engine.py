from types import SimpleNamespace

from core.self_healing.self_repair_engine import SelfRepairEngine


def _audit(*, readme_present: bool):
    return SimpleNamespace(
        name="example",
        origin="https://github.com/example/example.git",
        dirty=False,
        readme_present=readme_present,
    )


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
