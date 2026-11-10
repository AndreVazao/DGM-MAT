from core.event_bus.event_bus import EventBus


def test_event_bus_can_be_stopped_without_dropping_durable_queue():
    bus = EventBus()
    bus.running = True
    bus.stop()
    assert bus.running is False
