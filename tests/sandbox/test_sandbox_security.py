import pytest
from core.sandbox.isolated_runtime import IsolatedRuntime
from core.sandbox.execution_limits import ExecutionLimits

def test_sandbox_creation():
    runtime = IsolatedRuntime()
    sandbox = runtime.create_sandbox("test_task")
    assert "sandbox_test_task" in sandbox

def test_execution_limits():
    limits = ExecutionLimits()
    assert limits.check_limits({"cpu": 50})
    assert not limits.check_limits({"cpu": 95})
