from core.runtime.runtime_state_store import state_store, RuntimeTruthState
from core.realtime.websocket_manager import manager
import asyncio
import threading

def start_state_broadcaster():
    """
    Subscribes to StateStore changes and broadcasts them via WebSocket.
    """
    def on_state_change(snapshot: RuntimeTruthState):
        # We need to run the async broadcast in the existing event loop
        # For simplicity in this substrate, we'll use a helper that sends to the manager
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    manager.broadcast({"type": "state_update", "data": state_store.to_dict()}),
                    loop
                )
        except Exception:
            # Fallback if loop is not ready
            pass

    state_store.subscribe(on_state_change)
