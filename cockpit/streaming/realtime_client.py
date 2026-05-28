import asyncio
import json
import websockets
import time
import httpx
from typing import Callable, List, Optional
from core.observability.logger import dgm_logger

class RealtimeClient:
    def __init__(self, uri: str = "ws://localhost:8181/ws"):
        self.uri = uri
        self.http_uri = uri.replace("ws://", "http://").replace("/ws", "/health")
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.listeners: List[Callable[[dict], None]] = []
        self._running = False
        self.is_connected = False
        self.connection_state_callbacks: List[Callable[[bool, str], None]] = []
        self._retry_delay = 1.0
        self._max_retry_delay = 30.0
        self.last_reason = "UNKNOWN"

    def add_connection_callback(self, callback: Callable[[bool, str], None]):
        self.connection_state_callbacks.append(callback)

    def _update_connection_state(self, state: bool, reason: str = "UNKNOWN"):
        self.is_connected = state
        self.last_reason = reason
        for cb in self.connection_state_callbacks:
            try:
                # Support both 1 and 2 argument callbacks for backward compatibility if needed,
                # but we'll update MainWindow to use 2.
                cb(state, reason)
            except TypeError:
                cb(state)
            except Exception as e:
                dgm_logger.error(f"RealtimeClient: Connection state callback failed: {e}")

    async def _check_api_health(self) -> bool:
        """Checks if the HTTP API is reachable."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.http_uri, timeout=2.0)
                return response.status_code == 200
        except Exception:
            return False

    async def connect(self):
        """Establishes a persistent connection with exponential backoff and diagnostics."""
        self._running = True
        while self._running:
            try:
                dgm_logger.info(f"RealtimeClient: Attempting connection to {self.uri}...")
                async with websockets.connect(self.uri) as websocket:
                    self.websocket = websocket
                    self._retry_delay = 1.0 # Reset on success
                    self._update_connection_state(True, "CONNECTED")
                    dgm_logger.info(f"RealtimeClient: Connected to {self.uri}")

                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            self._notify_listeners(data)
                        except json.JSONDecodeError:
                            dgm_logger.warning(f"RealtimeClient: Received malformed message.")
            except Exception as e:
                # Diagnostics on failure
                api_alive = await self._check_api_health()
                reason = "API_DOWN" if not api_alive else "WS_DOWN"

                self._update_connection_state(False, reason)
                if self._running:
                    dgm_logger.error(f"RealtimeClient: Connection failed ({reason}: {e}). Retrying in {self._retry_delay:.1f}s")
                    await asyncio.sleep(self._retry_delay)
                    self._retry_delay = min(self._retry_delay * 2, self._max_retry_delay)

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
