from __future__ import annotations


def test_runtime_shutdown_cancels_startup_timers_and_stops_event_bus(monkeypatch):
    from core.runtime.runtime import Runtime
    from core.runtime.runtime_state_store import StateEvents

    class FakeTimer:
        cancelled = False

        def cancel(self):
            self.cancelled = True

    class FakeEventBus:
        stopped = False

        def stop(self, timeout=10.0):
            self.stopped = True
            return True

    class FakeStore:
        def __init__(self):
            self.events = []

        def dispatch(self, event, payload):
            self.events.append((event, payload))

    class FakeQueue:
        stopped = False

        def stop_consumer(self, timeout=5.0):
            self.stopped = True
            return True

    class FakeThread:
        alive = True
        joined = False

        def is_alive(self):
            return self.alive

        def join(self, timeout):
            assert timeout == 10
            self.joined = True
            self.alive = False

    timer = FakeTimer()
    event_bus = FakeEventBus()
    store = FakeStore()
    queue = FakeQueue()
    api_thread = FakeThread()
    runtime = Runtime.__new__(Runtime)
    runtime.repository_learning_service = None
    runtime.auto_help_worker = None
    runtime._startup_timers = [timer]
    runtime.api_thread = api_thread
    runtime.event_bus = event_bus
    runtime.state_store = store
    runtime.kernel = None
    runtime.governance_engine = None
    runtime._knowledge_engine = None
    monkeypatch.setattr("core.runtime.runtime.SafeActionQueue", lambda: queue)

    Runtime.shutdown(runtime)

    assert timer.cancelled is True
    assert runtime._startup_timers == []
    assert event_bus.stopped is True
    assert api_thread.joined is True
    assert queue.stopped is True
    assert store.events[-1][0] is StateEvents.COCKPIT_STATE_CHANGED
    assert store.events[-1][1]["runtime_status"] == "stopped"
