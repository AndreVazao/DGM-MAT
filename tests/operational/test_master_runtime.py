import pytest
from core.runtime.runtime import Runtime

def test_master_runtime_initialization():
    runtime = Runtime()
    assert runtime.state is not None
    assert runtime.kernel is not None
