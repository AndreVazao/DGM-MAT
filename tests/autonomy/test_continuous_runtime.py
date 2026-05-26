import pytest
import asyncio
from core.autonomy.continuous_runtime.runtime_core import ContinuousRuntime
from core.autonomy.continuous_runtime.cognition_scheduler import CognitionScheduler

@pytest.mark.asyncio
async def test_continuous_runtime_initialization():
    runtime = ContinuousRuntime()
    assert not runtime.active

    # Run for a very short time
    task = asyncio.create_task(runtime.run())
    await asyncio.sleep(0.1)
    assert runtime.active

    runtime.shutdown(None, None)
    await asyncio.sleep(0.1)
    assert not runtime.active

def test_cognition_scheduler():
    scheduler = CognitionScheduler()
    next_task = scheduler.get_next_task()
    assert next_task in ["observation", "planning", "execution", "reflection", "evolution"]
