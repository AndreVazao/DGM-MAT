import asyncio
import threading
from core.realtime.websocket_manager import (
    manager,
)
from core.observability.logger import dgm_logger

def safe_broadcast(message: dict):
    """
    Broadcasts a message to all connected clients in a thread-safe and loop-safe manner.
    """
    try:
        # 1. Attempt to get the current running loop
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                loop.create_task(manager.broadcast(message))
                return
        except RuntimeError:
            pass

        # 2. If no running loop in this thread, check if there's a global loop or run one-off
        # In a supervised environment, we usually have a main event loop somewhere.
        # For now, we use a simple fallback that works for both sync and async.

        def run_broadcast():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            new_loop.run_until_complete(manager.broadcast(message))
            new_loop.close()

        threading.Thread(target=run_broadcast, daemon=True).start()

    except Exception as e:
        dgm_logger.error(f"safe_broadcast: Failed to broadcast message: {e}")
