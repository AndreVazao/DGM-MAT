from core.runtime.runtime_state_store import state_store, RuntimeTruthState
from core.realtime.realtime_broadcast import safe_broadcast

def start_state_broadcaster():
    """
    Subscribes to StateStore changes and broadcasts them via WebSocket.
    """
    def on_state_change(snapshot: RuntimeTruthState):
        safe_broadcast({"type": "state_update", "data": state_store.to_dict()})

    state_store.subscribe(on_state_change)
