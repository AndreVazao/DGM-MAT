from datetime import datetime, timezone
from uuid import uuid4
from core.contracts.compat import event_to_contract
from core.storage.event_store import EventStore
from shared.models.event import Event

def make_event(kind=None):
    kind = kind or f"EVENT_REPLAY_TEST_{uuid4()}"
    return Event(id=str(uuid4()),timestamp=datetime.now(timezone.utc),source="test",target="core",
        event_type=kind,payload={"value":42},ttl=321,ecosystem="test",
        trace_id=str(uuid4()),parent_trace_id="parent-1",depth=2)

def test_event_maps_to_complete_public_envelope():
    e=make_event("EVENT_CONTRACT_MAP")
    c=event_to_contract(e)
    assert c.event_id==e.id and c.payload==e.payload
    assert c.ttl==321 and c.parent_trace_id=="parent-1" and c.depth==2 and c.ecosystem=="test"

def test_event_store_persists_and_replays_complete_envelope():
    e=make_event()
    EventStore.persist(e)
    stored=EventStore.get(e.id)
    assert stored is not None
    assert stored.event_id==e.id and stored.payload==e.payload
    assert stored.ttl==e.ttl and stored.parent_trace_id==e.parent_trace_id
    replayed=EventStore.replay(limit=20,event_type=e.event_type)
    assert any(x.event_id==e.id and x.depth==e.depth for x in replayed)
