import asyncio
from core.realtime.websocket_manager import (
    manager,
)

def safe_broadcast(message: dict):
    try:
        # If we are in the same loop (e.g. FastAPI context)
        loop = asyncio.get_running_loop()
        loop.create_task(
            manager.broadcast(message)
        )
    except RuntimeError:
        # Fallback for synchronous context
        # In a real app, we might want a persistent loop thread
        asyncio.run(
            manager.broadcast(message)
        )
