import pytest
import json
from core.autonomy.continuous_runtime.lifecycle_manager import LifecycleManager
from core.storage.storage_manager import storage_manager

def test_cognition_persistence_and_restore():
    manager = LifecycleManager()
    test_state = {"cycle": 42, "active_tasks": ["task_1", "task_2"]}

    # 1. Persist
    manager.persist_state(test_state)

    # 2. Restore
    restored = manager.restore_state()

    assert restored["cycle"] == 42
    assert "task_1" in restored["active_tasks"]

def test_interrupted_execution_recovery():
    # Simulate a crash by manually writing a state file
    crash_state = {"status": "EXECUTING", "task_id": "recovery_test"}
    storage_manager.save_data("sessions", "runtime_state.json", json.dumps(crash_state))

    manager = LifecycleManager()
    restored = manager.restore_state()

    assert restored["status"] == "EXECUTING"
    assert restored["task_id"] == "recovery_test"
