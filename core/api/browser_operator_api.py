"""Authenticated local queue API for visible-UI browser operator tasks."""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field

from core.providers.browser.browser_operator_queue import (
    BrowserOperatorQueue, BrowserOperatorQueueError,
)
from core.storage.storage_manager import storage_manager
from core.api.browser_capture_api import _validate_provider_url

router = APIRouter(prefix="/browser-operator", tags=["browser-operator"])


def _mission_status(mission_id: str) -> str | None:
    """Read the current durable parent checkpoint; never trust request-supplied state."""
    if not isinstance(mission_id, str) or not re.fullmatch(r"mission_[0-9a-f]{8}", mission_id):
        return None
    checkpoint = storage_manager.get_path("missions") / (mission_id + ".json")
    try:
        with checkpoint.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if data.get("mission_id") != mission_id:
            return None
        return data.get("status")
    except (OSError, ValueError, TypeError):
        return None


@lru_cache(maxsize=1)
def _queue() -> BrowserOperatorQueue:
    return BrowserOperatorQueue(
        storage_manager.get_path("tasks") / "browser_operator.sqlite3",
        mission_status_resolver=_mission_status,
    )


def _principal(request: Request) -> dict[str, Any]:
    principal = request.scope.get("state", {}).get("dgm_principal")
    if not isinstance(principal, dict) or not isinstance(principal.get("session_id"), str):
        raise HTTPException(status_code=401, detail="Authenticated local browser session required.")
    return principal


def _sync_mission_task(task_id: str, status: str, *, result: dict[str, Any] | None = None, error: str = "") -> None:
    task = _queue().get(task_id)
    if not task:
        return
    try:
        mission_id = str(task.get("mission_id") or "")
        from core.storage.storage_manager import storage_manager
        checkpoint = storage_manager.get_path("missions") / (mission_id + ".json")
        if not checkpoint.is_file():
            return
        from core.autonomy.mission_engine import mission_engine
        mission = mission_engine._reload_mission_checkpoint(mission_id)
        if mission is None:
            return
        mission.metadata["browser_operator_task_id"] = task_id
        mission.metadata["browser_operator_task_status"] = status
        if result is not None:
            assistant_text = result.get("assistant_text")
            if isinstance(assistant_text, str):
                mission.metadata["browser_operator_last_response"] = assistant_text[:1200]
            mission.metadata["browser_operator_last_result_status"] = str(result.get("status") or status)
        if error:
            mission.metadata["browser_operator_last_error"] = error[:500]
        mission_engine.save_mission(mission)
    except Exception:
        # The durable browser queue remains authoritative if mission checkpoint sync fails.
        return


class BrowserOperatorTaskCreate(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=200)
    mission_id: str = Field(min_length=1, max_length=80)
    provider: Literal["chatgpt", "gemini", "grok", "deepseek", "qwen"]
    source_id: str = Field(min_length=1, max_length=200)
    conversation_url: str = Field(min_length=12, max_length=2048)
    message: str = Field(min_length=1, max_length=30000)

    model_config = ConfigDict(extra="forbid")


class BrowserOperatorTaskResult(BaseModel):
    claim_token: str = Field(min_length=16, max_length=200)
    status: Literal["completed", "unverified"]
    result: dict[str, Any]

    model_config = ConfigDict(extra="forbid")


class BrowserOperatorTaskFailure(BaseModel):
    claim_token: str = Field(min_length=16, max_length=200)
    reason: str = Field(min_length=1, max_length=1000)
    blocked: bool = False

    model_config = ConfigDict(extra="forbid")


@router.post("/tasks", status_code=201)
def create_browser_operator_task(payload: BrowserOperatorTaskCreate, request: Request):
    principal = _principal(request)
    try:
        _validate_provider_url(payload.provider, payload.conversation_url, payload.source_id)
        task = _queue().enqueue(
            idempotency_key=payload.idempotency_key,
            mission_id=payload.mission_id,
            provider=payload.provider,
            source_id=payload.source_id,
            conversation_url=payload.conversation_url,
            message=payload.message,
            approval_required=True,
            created_by=str(principal.get("subject") or "local-operator"),
        )
    except (ValueError, BrowserOperatorQueueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if task.get("task_id"):
        _sync_mission_task(str(task["task_id"]), str(task.get("status") or "pending_approval"))
    return {
        "status": task.get("status"),
        "task_id": task.get("task_id"),
        "mission_id": task.get("mission_id"),
        "provider": task.get("provider"),
        "approval_required": task.get("status") == "pending_approval",
        "created_by": principal.get("subject", "local-operator"),
    }


@router.post("/tasks/{task_id}/approve")
def approve_browser_operator_task(task_id: str, request: Request):
    principal = _principal(request)
    if not _queue().approve(task_id, operator=str(principal.get("subject") or "local-operator")):
        raise HTTPException(status_code=409, detail="Task is missing or no longer awaiting approval.")
    _sync_mission_task(task_id, "queued")
    return {"status": "queued", "task_id": task_id}


@router.get("/next")
def claim_next_browser_operator_task(
    request: Request,
    provider: Literal["chatgpt", "gemini", "grok", "deepseek", "qwen"] = Query(...),
):
    principal = _principal(request)
    try:
        task = _queue().claim_next(
            provider=provider,
            worker_id=str(principal.get("session_id")),
        )
    except BrowserOperatorQueueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if task is None:
        return {"status": "queue_empty", "task": None}
    _sync_mission_task(str(task.get("task_id")), "claimed")
    return {"status": "claimed", "task": task}


@router.post("/tasks/{task_id}/result")
def complete_browser_operator_task(
    task_id: str, payload: BrowserOperatorTaskResult, request: Request,
):
    principal = _principal(request)
    if not _queue().complete(
        task_id,
        worker_id=str(principal.get("session_id")),
        claim_token=payload.claim_token,
        result=payload.result,
        status=payload.status,
    ):
        raise HTTPException(status_code=409, detail="Task claim is stale, expired or owned by another session.")
    _sync_mission_task(task_id, payload.status, result=payload.result)
    return {"status": payload.status, "task_id": task_id}


@router.post("/tasks/{task_id}/fail")
def fail_browser_operator_task(
    task_id: str, payload: BrowserOperatorTaskFailure, request: Request,
):
    principal = _principal(request)
    if not _queue().fail(
        task_id,
        worker_id=str(principal.get("session_id")),
        claim_token=payload.claim_token,
        reason=payload.reason,
        blocked=payload.blocked,
    ):
        raise HTTPException(status_code=409, detail="Task claim is stale, expired or owned by another session.")
    final_status = "blocked" if payload.blocked else "failed"
    _sync_mission_task(task_id, final_status, error=payload.reason)
    return {"status": final_status, "task_id": task_id}


@router.get("/tasks")
def list_browser_operator_tasks(request: Request, limit: int = Query(default=50, ge=1, le=200)):
    _principal(request)
    return {"tasks": _queue().list_tasks(limit=limit)}
