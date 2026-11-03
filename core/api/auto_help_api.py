"""Operator controls and status for asynchronous free-only AI help."""
from __future__ import annotations

from fastapi import APIRouter, Query

from core.api.mobile_bridge import auto_help_worker

router = APIRouter(prefix="/runtime/auto-help", tags=["autonomy-help"])


@router.get("")
def auto_help_status(limit: int = Query(default=10, ge=1, le=50)):
    return auto_help_worker.status() | {"recent": auto_help_worker.store.status(limit)["recent"]}


@router.post("/start")
def start_auto_help():
    started = auto_help_worker.start()
    return {
        "status": "started" if started else "already_running_or_disabled",
        "progress": auto_help_worker.status(),
    }


@router.post("/stop")
def stop_auto_help():
    auto_help_worker.stop()
    return {"status": "stopped", "progress": auto_help_worker.status()}
