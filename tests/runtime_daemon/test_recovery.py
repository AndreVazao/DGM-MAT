import pytest
import json
from pathlib import Path
from core.runtime_daemon.heartbeat import HeartbeatManager
from core.runtime_daemon.process_registry import ProcessRegistry

def test_heartbeat_corruption_recovery(tmp_path):
    hb_file = tmp_path / "heartbeat.json"
    hb_file.write_text("NOT_JSON")
    manager = HeartbeatManager(heartbeat_path=str(hb_file))

    # Should not crash on load
    last = manager.get_last_pulse()
    assert last == {}

    # Should recover by writing fresh pulse
    manager.pulse(status="recovered")
    assert hb_file.exists()
    assert json.loads(hb_file.read_text())["status"] == "recovered"

def test_registry_malformed_json(tmp_path):
    reg_file = tmp_path / "registry.json"
    reg_file.write_text("{ \"incomplete\": ")
    registry = ProcessRegistry(registry_path=str(reg_file))

    # Should not crash and return empty dict
    assert registry._load() == {}

    # Should recover and save fresh data
    registry.register_self("test")
    assert reg_file.exists()
    assert registry.get_pid("test") is not None
