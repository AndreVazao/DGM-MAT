from core.autonomy.autonomous_loop import AutonomousLoop


def test_loop_cycle():
    loop = AutonomousLoop()
    assert loop.run_cycle() is True
    assert "scan_001" in loop.scheduler.active_tasks


def test_config_loading():
    loop = AutonomousLoop()
    assert loop.config["enabled"] is True
