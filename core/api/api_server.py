# Path: C:\ProgramasGodMode\DGM-MAT\core\api\api_server.py
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from shared.config.settings import API_HOST, API_PORT
from core.realtime.websocket_manager import manager
from core.api.runtime_api import router as runtime_router
from core.api.mobile_bridge import router as mobile_router
from core.api.governance_api import router as governance_router


app = FastAPI(title="DGM-MAT API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(runtime_router)
app.include_router(mobile_router)
app.include_router(governance_router)


@app.get("/health")
def health():
    return {"status": "healthy", "service": "dgm-mat"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


def _mobile_ui_directory() -> Path | None:
    configured = os.getenv("DGM_MOBILE_UI_PATH")
    candidates = [
        Path(configured) if configured else None,
        Path(__file__).resolve().parents[3] / "DGM-MAT-Mobile" / "web",
    ]
    for candidate in candidates:
        if candidate and candidate.is_dir() and (candidate / "index.html").is_file():
            return candidate
    return None


mobile_ui = _mobile_ui_directory()
if mobile_ui:
    app.mount("/app", StaticFiles(directory=str(mobile_ui), html=True), name="mobile-app")


def run_api():
    import uvicorn

    uvicorn.run(app, host=API_HOST, port=API_PORT)
