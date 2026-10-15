import pytest
from core.runtime.runtime import Runtime

@pytest.mark.asyncio
async def test_runtime_init():
    # Verify core runtime object and truthful registration in the cockpit state store.
    runtime = Runtime()
    assert runtime is not None
    agents = runtime.state_store.get_snapshot().agents
    for role in ("repo", "provider", "autonomy"):
        record = agents[f"core:{role}"]
        assert record["role"] == role
        assert record["status"] == "initialized"
        assert record["implementation"]
