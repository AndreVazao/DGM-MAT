import asyncio
import json
from typing import Callable, List
from core.observability.logger import dgm_logger
from cockpit.streaming.realtime_client import RealtimeClient

class CockpitWebSocketClient:
    def __init__(self, url: str = "ws://localhost:8181/ws"):
        self.client = RealtimeClient(url)

    async def connect(self):
        dgm_logger.info("CockpitWSClient: Initializing realtime connection.")
        await self.client.connect()

    def on_message(self, callback: Callable):
        self.client.add_listener(callback)

    async def send_command(self, command: str, payload: dict):
        # Requirement 3: Exponential reconnect handled by RealtimeClient
        # This wrapper preserves the interface
        await self.client.send({
            "command": command,
            "payload": payload
        })

    def stop(self):
        self.client.stop()
