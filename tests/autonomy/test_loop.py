import pytest
from core.autonomy.autonomous_loop import AutonomousLoop
from pathlib import Path

def test_loop_cycle():
    loop = AutonomousLoop()
    loop.run_cycle()
    assert Path(".runtime/runtime_state.json").exists()

def test_config_loading():
    loop = AutonomousLoop()
    assert loop.config["enabled"] is True
