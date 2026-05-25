import pytest
from core.governance.execution_governor import execution_governor

def test_execution_authorization():
    # Safe operation
    auth = execution_governor.authorize_execution("labs/test", "Run unit tests")
    assert auth is True

    # Dangerous operation
    auth_dangerous = execution_governor.authorize_execution("labs/test", "rm -rf /")
    assert auth_dangerous is False

    # Core modification without system mode
    auth_core = execution_governor.authorize_execution("core/api", "Fix bug", {"execution_mode": "SAFE"})
    assert auth_core is False

def test_quarantine():
    execution_governor.quarantine_module("buggy_mod", "Constant crashes")
    assert execution_governor.is_quarantined("buggy_mod") is True
