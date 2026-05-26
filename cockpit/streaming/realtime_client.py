import asyncio
import json
import websockets
from typing import Callable, List, Optional
from core.observability.logger import dgm_logger

class RealtimeClient:
    def __init__(self, uri: str = "ws://localhost:8181/ws"):
        self.uri = uri
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.listeners: List[Callable[[dict], None]] = []
        self._running = False

    async def connect(self):
        """Establishes a persistent connection to the realtime server."""
        self._running = True
        while self._running:
            try:
                async with websockets.connect(self.uri) as websocket:
                    self.websocket = websocket
                    dgm_logger.info(f"RealtimeClient: Connected to {self.uri}")
                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            self._notify_listeners(data)
                        except json.JSONDecodeError:
                            dgm_logger.warning(f"RealtimeClient: Received malformed message: {message}")
            except Exception as e:
                dgm_logger.error(f"RealtimeClient: Connection error: {e}")
                if self._running:
                    await asyncio.sleep(5) # Retry after 5 seconds

    def _notify_listeners(self, data: dict):
        for listener in self.listeners:
            try:
                listener(data)
            except Exception as e:
                dgm_logger.error(f"RealtimeClient: Listener failed: {e}")

    def add_listener(self, listener: Callable[[dict], None]):
        self.listeners.append(listener)

    async def send(self, data: dict):
        if self.websocket and self.websocket.open:
            await self.websocket.send(json.dumps(data))
        else:
            dgm_logger.warning("RealtimeClient: Attempted to send data while disconnected.")

    def stop(self):
        self._running = False
