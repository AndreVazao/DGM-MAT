from core.self_healing.self_repair_engine import SelfRepairEngine


def test_apply_safe_never_executes_approval_gated_action(tmp_path, monkeypatch):
    engine = SelfRepairEngine(tmp_path / "example")
    action = {
        "id": "README-001",
        "category": "documentation",
        "risk": "LOW",
        "description": "Create a minimal truthful README from observed repository metadata.",
        "allowed_automatically": False,
        "command": None,
    }
    monkeypatch.setattr(engine, "diagnose", lambda: {"actions": [action]})

    def unexpected_execution(_action):
        raise AssertionError("Approval-gated action must never execute automatically")

    monkeypatch.setattr(engine, "_run_safe_action", unexpected_execution)

    result = engine.apply_safe(dry_run=False)

    assert result["applied"] == []
    assert result["skipped_for_approval"] == [action]
