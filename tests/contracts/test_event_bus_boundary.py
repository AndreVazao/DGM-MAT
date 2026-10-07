from datetime import datetime, timezone
from uuid import uuid4
from core.event_bus.event_bus import EventBus
from core.storage.event_store import EventStore
from shared.models.event import Event

def test_event_bus_persists_complete_envelope_before_dispatch():
    e=Event(id=str(uuid4()),timestamp=datetime.now(timezone.utc),source="test",target="core",
        event_type="EVENT_BUS_BOUNDARY_TEST",payload={"ok":True},ttl=777,ecosystem="test",depth=3)
    EventBus().publish(e)
    stored=EventStore.get(e.id)
    assert stored is not None and stored.event_id==e.id
    assert stored.payload=={"ok":True} and stored.ttl==777
    assert stored.ecosystem=="test" and stored.depth==3
