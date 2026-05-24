from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from shared.config.settings import (
    API_HOST,
    API_PORT,
)
from core.realtime.websocket_manager import (
    manager,
)
from core.api.runtime_api import router as runtime_router
from core.api.mobile_bridge import router as mobile_router

app = FastAPI(
    title="DGM-MAT API",
)

app.include_router(runtime_router)
app.include_router(mobile_router) # Phase 32: Mobile Bridge

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

def run_api():
    import uvicorn
    uvicorn.run(
        app,
        host=API_HOST,
        port=API_PORT,
    )
