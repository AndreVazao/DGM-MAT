import asyncio
import json
from typing import Callable, List
from core.observability.logger import dgm_logger

class CockpitWebSocketClient:
    def __init__(self, url: str):
        self.url = url
        self.listeners: List[Callable] = []

    async def connect(self):
        dgm_logger.info(f"CockpitWSClient: Connecting to {self.url}")
        # Simulated connection
        await asyncio.sleep(0.1)

    def on_message(self, callback: Callable):
        self.listeners.append(callback)

    def _simulate_message(self, data: str):
        for listener in self.listeners:
            listener(json.loads(data))
