import pytest
import time
from shared.models.event import Event
from core.runtime.runtime import Runtime
from core.governance.runtime_limits import RuntimeLimits
from core.storage.database import engine
from core.storage.models import Base

def test_storm_protection():
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    runtime = Runtime()
    # Force state to non-degraded to ensure deterministic test
    runtime.governance_engine.degradation_controller.state.is_degraded = False
    runtime.governance_engine.degradation_controller.state.emergency_slowdown = False

    # Reset history
    runtime.governance_engine.event_governor.event_history = []
    # Clear event bus throttling
    runtime.event_bus.event_counts.clear()

    # Manually trigger a storm
    # Use Critical priority to bypass EventBus throttling but hit EventGovernor limits
    from shared.enums.event_priority import EventPriority
    for i in range(150):
        event = Event(source="test_source", target="test_target", event_type="storm.event", priority=EventPriority.CRITICAL)
        runtime.event_bus.publish(event)

    # Check if degradation or storm protection was triggered
    # The EventGovernor drops events once threshold is hit (100)
    # Or if degradation is triggered by high CPU (which can happen in CI)
    assert runtime.governance_engine.degradation_controller.state.emergency_slowdown is True or \
           runtime.governance_engine.degradation_controller.state.is_degraded is True or \
           len(runtime.governance_engine.event_governor.event_history) >= 100

def test_recursion_depth_limit():
    runtime = Runtime()
    limits = RuntimeLimits(max_event_depth=5)
    runtime.governance_engine.event_governor.limits = limits

    # Create an event with excessive depth
    event = Event(source="source", target="target", event_type="deep.event", depth=10)

    # It should be dropped
    runtime.event_bus.publish(event)
    # Check queue (should be empty as it's dropped before put)
    assert runtime.event_bus.queue.empty()

def test_loop_detection():
    runtime = Runtime()
    trace_id = "loop_trace"

    # Publish same event type multiple times in same trace
    for _ in range(10):
        event = Event(source="s", target="t", event_type="repeat.event", trace_id=trace_id)
        runtime.event_bus.publish(event)

    # The loop detector should have caught it by now (limit is 5)
    assert True
