from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from core.realtime.websocket_manager import manager
from core.observability.logger import dgm_logger

router = APIRouter(prefix="/mobile", tags=["mobile"])

@router.get("/status")
async def get_mobile_status():
    return {"status": "ready", "bridge": "active"}

@router.websocket("/ws")
async def mobile_websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    dgm_logger.info("Mobile Bridge: WebSocket connected.")
    try:
        while True:
            data = await websocket.receive_json()
            dgm_logger.info(f"Mobile Bridge: Received data: {data}")
            # Handle mobile commands
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        dgm_logger.info("Mobile Bridge: WebSocket disconnected.")
