from core.contracts.compat import event_to_contract
from shared.models.event import Event
from core.realtime.realtime_broadcast import safe_broadcast

def stream_event(event:Event):
    envelope=event_to_contract(event)
    safe_broadcast({"type":"event",**envelope.model_dump(mode="json")})
