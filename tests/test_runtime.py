import pytest
from datetime import datetime
from core.runtime.runtime import Runtime
from shared.models.event import Event
from core.validation.event_validator import EventValidator, EventValidationError

def test_runtime_bootstrap():
    runtime = Runtime()
    # We don't want to start the API in tests if it blocks or causes issues
    # but we can check if the components are initialized
    assert runtime.event_bus is not None
    assert runtime.overseer is not None
    assert runtime.repo_agent is not None

def test_event_validation():
    # Valid event
    event = Event(source="test", target="test", event_type="test")
    EventValidator.validate(event)

    # Invalid event
    with pytest.raises(EventValidationError):
        bad_event = Event(source="", target="test", event_type="test")
        EventValidator.validate(bad_event)

def test_storage_persistence():
    from core.storage.event_store import EventStore
    from core.storage.database import SessionLocal
    from core.storage.models import EventRecord
    import json

    event = Event(
        source="test_source",
        target="test_target",
        event_type="test_event",
        payload={"key": "value"}
    )

    EventStore.persist(event)

    db = SessionLocal()
    try:
        record = db.query(EventRecord).filter_by(event_id=event.id).first()
        assert record is not None
        assert record.source == "test_source"
        assert json.loads(record.payload) == {"key": "value"}
    finally:
        db.close()
