[Reading 144 lines from start (total: 144 lines, 0 remaining)]

# Path: C:\ProgramasGodMode\DGM-MAT\core\api\mobile_bridge.py
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.mobile_runtime import MobileConversationService
from core.organization import CapabilityScout


router = APIRouter(prefix="/mobile", tags=["mobile"])
service = MobileConversationService()
capability_scout = CapabilityScout()


class ThreadCreateRequest(BaseModel):
    title: str = "Nova conversa"
    project: str | None = None
    repository: str | None = None


class MessageRequest(BaseModel):
    content: str


class RenameRequest(BaseModel):
    title: str


class CapabilityScoutRequest(BaseModel):
    capability: str
    reason: str
    mission_id: str = "mission:mobile-capability-scout"
    required_skills: list[str] = []


def _tailscale_identity() -> dict:
    try:
        raw = subprocess.check_output(
            ["tailscale", "status", "--json"],
            text=True,
            timeout=3,
        )
        payload = json.loads(raw)
        self_node = payload.get("Self", {})
        dns_name = str(self_node.get("DNSName") or "").rstrip(".")
        ips = self_node.get("TailscaleIPs") or []
        ipv4 = next((ip for ip in ips if "." in str(ip)), None)
        return {
            "online": bool(self_node.get("Online")),
            "hostname": self_node.get("HostName"),
            "dns_name": dns_name,
            "ipv4": ipv4,
            "https_endpoint": f"https://{dns_name}" if dns_name else None,
        }
    except (OSError, subprocess.SubprocessError, ValueError):
        return {"online": False, "hostname": None, "dns_name": None, "ipv4": None, "https_endpoint": None}


def _ollama_status() -> dict:
    try:
        from urllib.request import urlopen

        with urlopen("http://127.0.0.1:11434/api/tags", timeout=2) as response:
            payload = json.loads(response.read().decode("utf-8"))
        models = [item.get("name") for item in payload.get("models", [])]
        return {"available": True, "models": [m for m in models if m]}
    except (OSError, ValueError):
        return {"available": False, "models": []}


@router.get("/status")
def get_mobile_status():
    tailscale = _tailscale_identity()
    return {
        "status": "ready",
        "bridge": "active",
        "chat": "continuous-thread",
        "intent": "enabled",
        "storage": "local-durable",
        "tailscale": tailscale,
        "ollama": _ollama_status(),
        "source_of_truth": "authorized-dgm-mat-pc",
    }


@router.get("/threads")
def list_threads():
    return {"threads": service.list_threads()}


@router.post("/threads")
def create_thread(request: ThreadCreateRequest):
    return service.create_thread(
        request.title,
        project=request.project,
        repository=request.repository,
    )


@router.get("/threads/{thread_id}")
def get_thread(thread_id: str):
    thread = service.get_thread(thread_id)
    if thread is None:
        raise HTTPException(status_code=404, detail="Conversation thread not found")
    return thread


@router.post("/threads/{thread_id}/messages")
def append_message(thread_id: str, request: MessageRequest):
    content = request.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Message content is required")
    try:
        return service.append_user_message(thread_id, content)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Conversation thread not found") from exc


@router.post("/threads/{thread_id}/rename")
def rename_thread(thread_id: str, request: RenameRequest):
    title = request.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Title is required")
    try:
        return service.rename(thread_id, title)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Conversation thread not found") from exc


@router.get("/capabilities")
def mobile_capabilities():
    return {
        "schema": "dgm-mat.mobile-capabilities.v1",
        "features": [
            "continuous-conversations",
            "thread-history",
            "rename-conversation",
            "intent-understanding",
            "durable-local-history",
            "tailscale-direct",
            "vercel-discovery",
            "offline-pwa-shell",
            "local-ollama-assist",
        ],
        "execution_authority": "dgm-mat-pc",
        "cloud_role": "rendezvous-only",
    }

[executed on device: PC-Vazao-Anjos (982eb058-a42c-4897-9732-547f04cb44f0)]

@router.post("/capability-scout")
def capability_scout_discover(request: CapabilityScoutRequest):
    capability = request.capability.strip()
    reason = request.reason.strip()
    if not capability or not reason:
        raise HTTPException(status_code=400, detail="Capability and reason are required")
    return capability_scout.discover(
        capability,
        reason,
        mission_id=request.mission_id,
        required_skills=request.required_skills,
    )
