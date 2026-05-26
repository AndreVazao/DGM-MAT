from typing import Dict, Any
from core.cockpit_runtime.websocket_runtime import WebSocketRuntime

class CognitionVisualizer:
    def __init__(self, ws_runtime: WebSocketRuntime):
        self.ws = ws_runtime

    async def visualize_cycle(self, cycle_data: Dict[str, Any]):
        await self.ws.broadcast({
            "type": "cognition_cycle",
            "data": cycle_data
        })
