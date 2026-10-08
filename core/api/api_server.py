# Path: C:\ProgramasGodMode\DGM-MAT\core\api\api_server.py
from __future__ import annotations

import json
import os
import subprocess
import threading
import time
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from shared.config.settings import API_HOST, API_PORT
from core.realtime.websocket_manager import manager
from core.api.runtime_api import router as runtime_router
from core.api.mobile_bridge import router as mobile_router
from core.api.governance_api import router as governance_router
from core.federation.node_identity import local_node
from core.federation.rendezvous_client import RendezvousClient


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


def _tailscale_endpoint() -> str | None:
    try:
        payload = json.loads(
            subprocess.check_output(
                ["tailscale", "status", "--json"],
                text=True,
                timeout=3,
            )
        )
        self_node = payload.get("Self", {})
        dns_name = str(self_node.get("DNSName") or "").rstrip(".")
        if dns_name:
            return "https://" + dns_name
        ipv4 = next(
            (str(ip) for ip in self_node.get("TailscaleIPs", []) if "." in str(ip)),
            None,
        )
        return "http://" + ipv4 + ":8181" if ipv4 else None
    except (OSError, subprocess.SubprocessError, ValueError):
        return None


def _register_rendezvous() -> None:
    try:
        endpoint = _tailscale_endpoint()
        RendezvousClient().register(
            node_id=local_node.node_id,
            node_type="home-pc",
            name=local_node.hostname,
            endpoint=endpoint,
            capabilities=[
                "api",
                "cockpit",
                "mobile-chat",
                "conversation-intelligence",
                "filesystem",
                "git",
                "telescope",
                "ollama-local-ai",
            ],
            version="phase-45-mobile-cockpit",
            ttl_seconds=180,
        )
    except Exception:
        return


def _rendezvous_heartbeat() -> None:
    while True:
        _register_rendezvous()
        time.sleep(60)


@app.on_event("startup")
def start_rendezvous_heartbeat() -> None:
    thread = threading.Thread(
        target=_rendezvous_heartbeat,
        name="dgm-rendezvous-heartbeat",
        daemon=True,
    )
    thread.start()


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
