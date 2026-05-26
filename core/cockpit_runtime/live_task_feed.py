from typing import Dict, Any
from core.cockpit_runtime.websocket_runtime import WebSocketRuntime

class LiveTaskFeed:
    def __init__(self, ws_runtime: WebSocketRuntime):
        self.ws = ws_runtime

    async def update_task(self, task_id: str, status: str):
        await self.ws.broadcast({
            "type": "task_update",
            "task_id": task_id,
            "status": status
        })
