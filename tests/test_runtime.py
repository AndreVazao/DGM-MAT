from core.runtime.runtime import Runtime
from shared.models.event import Event

def test_runtime_bootstrap():
    runtime = Runtime()
    # Mocking or just checking if it runs without error
    runtime.bootstrap()
    assert runtime.overseer.processed_events == 1

def test_event_validation():
    from core.validation.event_validator import EventValidator, EventValidationError
    import pytest

    event = Event(source="", target="test", event_type="test")
    with pytest.raises(EventValidationError):
        EventValidator.validate(event)
