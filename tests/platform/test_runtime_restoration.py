import pytest
from core.runtime.runtime import Runtime

@pytest.mark.asyncio
async def test_runtime_init():
    # Verify core runtime object
    runtime = Runtime()
    assert runtime is not None
