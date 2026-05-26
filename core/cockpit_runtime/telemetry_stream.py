import asyncio
from typing import Dict, Any
from core.observability.logger import dgm_logger
from core.cockpit_runtime.websocket_runtime import WebSocketRuntime

class TelemetryStream:
    def __init__(self, ws_runtime: WebSocketRuntime):
        self.ws = ws_runtime

    async def stream_metrics(self, metrics: Dict[str, Any]):
        await self.ws.broadcast({
            "type": "telemetry",
            "data": metrics
        })
