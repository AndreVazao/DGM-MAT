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
from core.api.usb_recovery_api import router as usb_recovery_router
from core.operator.usb_recovery import start_usb_recovery_monitor
from core.api.governance_api import router as governance_router
from core.api.provider_execution_api import router as provider_execution_router
from core.api.local_auth_api import router as local_auth_router, session_manager
from core.api.auth_middleware import LocalSessionAuthMiddleware
from core.federation.node_identity import local_node
from core.federation.rendezvous_client import RendezvousClient


app = FastAPI(title="DGM-MAT API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8181", "http://localhost:8181", "https://localhost"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-DGM-Governance-Credential"],
)

app.include_router(runtime_router)
app.include_router(mobile_router)
app.include_router(usb_recovery_router)
app.include_router(governance_router)
app.include_router(provider_execution_router)
app.include_router(local_auth_router)


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


RENDEZVOUS_ENABLED_ENV = "DGM_RENDEZVOUS_ENABLED"
RENDEZVOUS_INTERVAL_ENV = "DGM_RENDEZVOUS_INTERVAL_SECONDS"
DEFAULT_RENDEZVOUS_INTERVAL_SECONDS = 20 * 60


def _rendezvous_interval_seconds() -> int:
    """Return a bounded heartbeat interval; default to 20 minutes."""
    try:
        configured = int(os.getenv(RENDEZVOUS_INTERVAL_ENV, str(DEFAULT_RENDEZVOUS_INTERVAL_SECONDS)))
    except (TypeError, ValueError):
        configured = DEFAULT_RENDEZVOUS_INTERVAL_SECONDS
    return max(60, min(configured, 24 * 60 * 60))


def _rendezvous_heartbeat() -> None:
    interval = _rendezvous_interval_seconds()
    while True:
        _register_rendezvous()
        time.sleep(interval)


@app.on_event("startup")
def start_rendezvous_heartbeat() -> None:
    # Disabled by default until mobile/federation deployment is intentionally activated.
    if os.getenv(RENDEZVOUS_ENABLED_ENV, "0").strip().lower() not in {"1", "true", "yes", "on"}:
        return
    thread = threading.Thread(
        target=_rendezvous_heartbeat,
        name="dgm-rendezvous-heartbeat",
        daemon=True,
    )
    thread.start()


@app.on_event("startup")
def start_usb_recovery() -> None:
    # The monitor only performs safe ADB reconnection; it never wipes app/device data.
    start_usb_recovery_monitor()


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

# Enforce the route inventory after all HTTP/WebSocket routes and the optional UI mount are registered.
# Keep this middleware outermost; it validates sessions before route handlers run.
app.add_middleware(
    LocalSessionAuthMiddleware,
    routes=app.router.routes,
    session_manager=session_manager,
)


def run_api():
    import uvicorn

    uvicorn.run(app, host=API_HOST, port=API_PORT)
