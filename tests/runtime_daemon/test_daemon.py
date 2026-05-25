import pytest
from core.runtime_daemon.heartbeat import HeartbeatManager
from core.runtime_daemon.process_registry import ProcessRegistry

def test_heartbeat_pulse(tmp_path):
    hb_file = tmp_path / "heartbeat.json"
    manager = HeartbeatManager(heartbeat_path=str(hb_file))
    manager.pulse(status="test")
    assert hb_file.exists()
    pulse = manager.get_last_pulse()
    assert pulse["status"] == "test"

def test_process_registry(tmp_path):
    reg_file = tmp_path / "registry.json"
    registry = ProcessRegistry(registry_path=str(reg_file))
    registry.register_self("test-proc")
    assert reg_file.exists()
    assert registry.get_pid("test-proc") is not None
