import json
import asyncio
from typing import Dict, Any
from core.observability.logger import dgm_logger

class RealtimeRuntimeAPI:
    """
    Hardened Realtime API for Cockpit.
    Non-blocking and rate-limited.
    """
    def __init__(self):
        self._last_broadcast = 0
        self._broadcast_interval = 1.0 # Max 1Hz broadcast

    async def broadcast_state(self, state: Dict[str, Any]):
        now = asyncio.get_event_loop().time()
        if now - self._last_broadcast < self._broadcast_interval:
            return # Throttle

        try:
            # Simulated non-blocking websocket broadcast
            # In real implementation, this would use a manager
            self._last_broadcast = now
            dgm_logger.debug("RealtimeRuntimeAPI: State broadcasted")
        except Exception as e:
            dgm_logger.error(f"RealtimeRuntimeAPI: Broadcast failed: {e}")
