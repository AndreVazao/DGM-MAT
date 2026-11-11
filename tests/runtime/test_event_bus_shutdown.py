from threading import Event

from core.event_bus.event_bus import EventBus
from shared.models.event import Event as DgmEvent


def test_event_bus_stop_joins_worker_after_current_queue_drain():
    bus = EventBus()
    delivered = Event()
    bus.subscribe("shutdown.test", lambda event: delivered.set())
    bus.start()
    bus.publish(DgmEvent(
        source="test",
        target="test",
        event_type="shutdown.test",
        payload={},
    ))

    assert delivered.wait(2.0)
    assert bus.stop(timeout=2.0) is True
    assert bus._worker_thread is not None
    assert not bus._worker_thread.is_alive()
    assert bus.queue.empty()
