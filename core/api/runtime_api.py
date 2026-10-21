# Path: C:\ProgramasGodMode\DGM-MAT\core\api\runtime_api.py

import json
import os
import re
import time
from datetime import datetime
import psutil
from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from core.storage.storage_manager import storage_manager
from core.repository_cognition.repo_scanner import CognitiveRepoScanner
from core.autonomy.mission_engine import mission_engine
from core.autonomy.mission_models import MissionStatus
from core.workspace.workspace_manager import workspace_manager
from core.connectors.boundary import create_runtime_connectors
from core.runtime.runtime_state_store import state_store, StateEvents
from core.runtime.safe_action_queue import SafeActionQueue
from core.execution.approval_manager import ApprovalManager
from core.provider_sync.provider_registry import provider_registry
from core.runtime.reality_snapshot import RealitySnapshotService
from core.runtime.provider_freshness import (
    PROVIDER_OBSERVATION_STALE_AFTER_SECONDS,
    provider_freshness as _shared_provider_freshness,
)
from core.realtime.websocket_manager import manager

router = APIRouter(prefix="/runtime", tags=["runtime"])
connectors = create_runtime_connectors()
obsidian_connector = connectors["obsidian"]

class MissionCreate(BaseModel):
    goal: str = Field(min_length=1, max_length=2000)
    description: Optional[str] = ""

    @field_validator("goal")
    @classmethod
    def require_nonblank_goal(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("goal must contain non-whitespace characters")
        return normalized

class ApprovalDecision(BaseModel):
    decision: str # "approve" or "reject"

class QueueRejection(BaseModel):
    reason: str = Field(min_length=3, max_length=500)

@router.websocket("/ws")
async def runtime_websocket_endpoint(websocket: WebSocket):
    """Compatibility websocket for clients that connect to /runtime/ws."""
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@router.get("/health")
def get_runtime_health():
    """Unified health endpoint pulling from state_store."""
    truth = state_store.get_snapshot()
    return truth.health or {"status": "unknown"}

@router.get("/status")
def get_runtime_status():
    """Comprehensive status pulling from state_store."""
    truth = state_store.get_snapshot()
    return {
        "status": truth.runtime_status,
        "is_degraded": truth.is_degraded,
        "resources": {
            "cpu": psutil.cpu_percent(),
            "memory": psutil.virtual_memory().percent
        },
        "agents": truth.agents,
        "missions_active": len(truth.missions)
    }

@router.get("/state")
def get_runtime_state():
    """Compatibility endpoint for cockpit clients that request /runtime/state."""
    return state_store.to_dict()

@router.get("/truth")
def get_runtime_truth():
    """Requirement 2: Expose single source of truth."""
    return state_store.to_dict()

@router.get("/reality")
def get_runtime_reality():
    """Expose observed reality with provider freshness applied at serialization time."""
    return state_store.to_dict().get("reality", {})

@router.get("/degradation")
def get_runtime_degradation():
    """Requirement 4: Expose degradation details."""
    truth = state_store.get_snapshot()
    return {
        "is_degraded": truth.is_degraded,
        "degradation": truth.degradation
    }

@router.get("/repo_scan")
def get_repo_scan():
    """Restored for compatibility with existing tests."""
    scanner = CognitiveRepoScanner()
    try:
        results = scanner.scan()
        return {"status": "success", "files_scanned": len(results), "results": results[:100]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/memory/stats")
def get_memory_stats():
    """Restored for compatibility with existing tests."""
    return state_store.get_snapshot().memory_stats

@router.get("/memory")
def get_memory_status():
    memory_stats = state_store.get_snapshot().memory_stats
    return {
        "status": "recognized",
        "manager": "core.memory.memory_manager",
        "stats": memory_stats,
    }

def _provider_freshness(provider: Dict[str, Any], now: Optional[float] = None) -> Dict[str, Any]:
    """Compatibility wrapper for the shared provider-freshness contract."""
    return _shared_provider_freshness(provider, now=now)


def _provider_subsystem_summary(registered: List[str], providers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Describe registry state without confusing API success with provider health."""
    observed_providers = [
        provider for provider in providers
        if provider.get("availability_observed") is True
    ]
    stale_observations = [
        provider for provider in observed_providers
        if provider.get("freshness_status") == "stale"
    ]
    reported_available_count = sum(
        1 for provider in observed_providers if provider.get("available") is True
    )

    if not registered:
        state = "empty_registry"
    elif observed_providers and len(stale_observations) == len(observed_providers):
        state = "stale_availability_observations"
    elif observed_providers:
        state = "availability_reported"
    else:
        state = "registered_no_availability_reported"

    return {
        "state": state,
        "registered_count": len(registered),
        "registered_names": list(registered),
        "availability_observation_count": len(observed_providers),
        "stale_observation_count": len(stale_observations),
        "reported_available_count": reported_available_count,
        "availability_reported": bool(observed_providers),
        "source": "state_store_or_reality_snapshot",
    }


@router.get("/providers")
def list_providers():
    snapshot = state_store.get_snapshot()
    providers = list(snapshot.providers.values())

    if not providers:
        providers = RealitySnapshotService()._get_providers_status()
        state_store.dispatch(StateEvents.PROVIDERS_RECONCILED, {
            "providers": providers,
            "observed_at": time.time(),
        })

    providers = [_provider_freshness(provider) for provider in providers]
    registered = provider_registry.list_providers()
    return {
        "status": "success",
        "providers": providers,
        "registered": registered,
        "provider_subsystem": _provider_subsystem_summary(registered, providers),
    }

@router.get("/governance")
def get_governance_status():
    truth = state_store.get_snapshot()
    resources = {
        "cpu": psutil.cpu_percent(),
        "memory": psutil.virtual_memory().percent,
    }
    return {
        "status": truth.degradation.get("status", "unknown"),
        "is_degraded": truth.is_degraded,
        "resources": resources,
        "degradation": truth.degradation,
    }

@router.get("/autonomy")
def get_autonomy_status():
    truth = state_store.get_snapshot()
    return {
        "status": truth.runtime_status,
        "mode": "LOW_MEMORY" if truth.health.get("low_memory_profile") else "STANDARD",
        "missions_active": len(truth.missions),
        "tasks": truth.tasks,
        "memory_stats": truth.memory_stats,
    }

@router.get("/workspace/scan")
def scan_workspace():
    """Requirement 4: Automatic repository discovery and health scan."""
    return workspace_manager.scan_workspace()

@router.get("/obsidian/index")
def index_obsidian():
    """Requirement 6: Obsidian vault indexing."""
    return obsidian_connector.index_vault()

@router.post("/missions")
def create_mission(mission_data: MissionCreate):
    """Requirement 7: Mission creation interface."""
    # Creation is not execution: expose validation failure truthfully to callers.
    mission = mission_engine.create_mission(mission_data.goal, mission_data.description)
    if mission.status.value == "FAILED":
        return {
            "status": "failed",
            "mission_id": mission.mission_id,
            "error": mission.error or "Mission validation failed.",
        }
    action_id = mission.metadata.get("action_id")
    action = SafeActionQueue().get_action(action_id) if action_id else None
    return {
        "status": "success",
        "mission_id": mission.mission_id,
        "mission_status": mission.status.value,
        "action_id": action_id,
        "action_status": action.get("status") if action else None,
    }

@router.get("/missions")
def list_missions():
    """Return mission status from durable checkpoints, not a potentially stale process cache."""
    missions = []
    for mission_id in list(mission_engine.active_missions):
        mission = mission_engine._reload_mission_checkpoint(mission_id)
        if mission is None:
            continue
        action_id = mission.metadata.get("action_id")
        action = SafeActionQueue().get_action(action_id) if action_id else None
        missions.append({
            "mission_id": mission.mission_id,
            "goal": mission.goal,
            "status": mission.status.value,
            "created_at": mission.created_at.isoformat() if mission.created_at else None,
            "progress": mission.progress,
            "logs": mission.logs,
            "error": mission.error,
            "metadata": mission.metadata,
            "action_id": action_id,
            "action_status": action.get("status") if action else None,
            "result": mission.metadata.get("result"),
            "output": mission.metadata.get("output"),
        })
    return missions


@router.get("/missions/{mission_id}")
def get_mission_detail(mission_id: str):
    """Return one durable mission checkpoint without mutating runtime state."""
    if not re.fullmatch(r"mission_[0-9a-f]{8}", mission_id):
        raise HTTPException(status_code=404, detail="Mission checkpoint not found")

    mission_file = mission_engine.missions_path / f"{mission_id}.json"
    try:
        data = json.loads(mission_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise HTTPException(status_code=404, detail="Mission checkpoint not found")

    if not isinstance(data, dict) or data.get("mission_id") != mission_id:
        raise HTTPException(status_code=404, detail="Mission checkpoint not found")

    status = data.get("status")
    if isinstance(status, dict):
        status = status.get("value")
    valid_statuses = {item.value for item in MissionStatus}
    if not isinstance(status, str) or status not in valid_statuses:
        raise HTTPException(status_code=404, detail="Mission checkpoint is invalid")

    metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
    result = metadata.get("result")
    output = metadata.get("output")
    result_truncated = False
    output_truncated = False

    def bound_value(value, limit=24000):
        nonlocal result_truncated, output_truncated
        if value is None:
            return None
        try:
            encoded = json.dumps(value, ensure_ascii=False, default=str)
        except (TypeError, ValueError):
            encoded = str(value)
        if len(encoded) <= limit:
            return value
        preview = encoded[:limit]
        if value is result:
            result_truncated = True
        if value is output:
            output_truncated = True
        return {"truncated": True, "preview": preview}

    action_id = metadata.get("action_id")
    if isinstance(action_id, bool) or not isinstance(action_id, int):
        action_id = None
    action = SafeActionQueue().get_action(action_id) if action_id is not None else None
    result_data = result if isinstance(result, dict) else {}
    return {
        "mission_id": mission_id,
        "status": status,
        "progress": data.get("progress"),
        "created_at": data.get("created_at"),
        "updated_at": data.get("updated_at"),
        "action_id": action_id,
        "action_status": action.get("status") if action else None,
        "handler": result_data.get("handler") if isinstance(result_data.get("handler"), str) else None,
        "result": bound_value(result),
        "output": bound_value(output),
        "result_truncated": result_truncated,
        "output_truncated": output_truncated,
        "error": data.get("error") if isinstance(data.get("error"), str) else None,
        "source": "durable_mission_checkpoint",
    }


@router.get("/office/telemetry")
def get_office_telemetry():
    """Read-only, content-minimized telemetry for the virtual office projection."""
    status_counts = {status.value: 0 for status in MissionStatus}
    recent_missions = []
    invalid_checkpoints = 0

    # Read durable mission checkpoints directly; this endpoint must not refresh or
    # mutate mission state merely because the visual cockpit opened.
    for checkpoint in mission_engine.missions_path.glob("*.json"):
        try:
            data = json.loads(checkpoint.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("checkpoint must be an object")
            mission_id = data.get("mission_id", checkpoint.stem)
            status = data.get("status")
            if isinstance(status, dict):
                status = status.get("value")
            if (
                not isinstance(mission_id, str) or not mission_id
                or not isinstance(status, str) or status not in status_counts
            ):
                raise ValueError("checkpoint identity/status is invalid")
            metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
            result = metadata.get("result") if isinstance(metadata.get("result"), dict) else {}
            updated_at = data.get("updated_at") or data.get("created_at")
            action_id = metadata.get("action_id")
            if isinstance(action_id, bool) or not isinstance(action_id, int):
                action_id = None
            status_counts[status] += 1
            recent_missions.append({
                "mission_id": mission_id,
                "status": status,
                "updated_at": updated_at if isinstance(updated_at, str) else None,
                "action_id": action_id,
                "handler": result.get("handler") if isinstance(result.get("handler"), str) else None,
            })
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
            invalid_checkpoints += 1

    recent_missions.sort(key=lambda item: item.get("updated_at") or "", reverse=True)
    recent_missions = recent_missions[:8]

    queue = SafeActionQueue()
    action_telemetry = queue.get_mission_execution_telemetry(limit=8)
    queue_health = queue.get_health()
    snapshot = state_store.get_snapshot()
    active_missions = status_counts.get(MissionStatus.RUNNING.value, 0)
    waiting_missions = sum(status_counts.get(status, 0) for status in (
        MissionStatus.QUEUED.value, MissionStatus.APPROVAL_PENDING.value,
        MissionStatus.WAITING_FOR_USER.value,
    ))
    action_counts = action_telemetry.get("counts", {})
    queued_actions = int(action_counts.get("QUEUED", 0))
    approved_actions = int(action_counts.get("APPROVED", 0))
    running_actions = int(action_counts.get("RUNNING", 0))

    engineering_state = "active" if active_missions else ("waiting" if waiting_missions else "idle")
    approvals_state = "waiting" if queued_actions else ("active" if approved_actions or running_actions else "idle")
    worker_alive = queue_health.get("worker_alive") is True

    return {
        "schema": "dgm-mat.office-telemetry.v1",
        "generated_at": datetime.now().isoformat(),
        "source": "durable_mission_checkpoints+safe_action_queue+runtime_state_store",
        "runtime": {
            "status": getattr(snapshot, "runtime_status", "unknown"),
            "is_degraded": bool(getattr(snapshot, "is_degraded", False)),
        },
        "missions": {
            "total": sum(status_counts.values()),
            "counts": status_counts,
            "invalid_checkpoints": invalid_checkpoints,
            "recent": recent_missions,
        },
        "actions": action_telemetry,
        "queue_worker": {
            "worker_alive": worker_alive,
            "last_heartbeat": queue_health.get("last_heartbeat"),
            "registered_handler_count": len(queue_health.get("handlers", [])),
        },
        "departments": {
            "engineering": {
                "state": engineering_state,
                "active_missions": active_missions,
                "waiting_missions": waiting_missions,
                "reason": "Derived from persisted mission checkpoint states.",
            },
            "approvals": {
                "state": approvals_state,
                "waiting_decisions": queued_actions,
                "approved_actions": approved_actions,
                "running_actions": running_actions,
                "reason": "Derived from durable MISSION_EXECUTION queue states.",
            },
            "operations": {
                "state": "active" if worker_alive else "unknown",
                "worker_alive": worker_alive,
                "reason": "Worker state is unknown when no live consumer heartbeat is available.",
            },
            "research": {
                "state": "unknown",
                "reason": "No department-specific research event feed is registered yet.",
            },
            "memory": {
                "state": "unknown",
                "reason": "No department-specific memory event feed is registered yet.",
            },
            "agents": {
                "state": "unknown",
                "reason": "No per-agent activity event feed is registered yet.",
            },
        },
        "limitations": [
            "This endpoint is observational and does not authorize, approve, execute, or mutate missions.",
            "Mission goals, conversation content, credentials, and full action payloads are intentionally omitted.",
            "Unknown departments remain unknown until a real event source is registered.",
        ],
    }


@router.post("/approvals/{request_id}")
def judge_approval(request_id: str, decision: ApprovalDecision):
    """Requirement 7: Functional approval/reject workflow."""
    success = mission_engine.handle_approval_decision(request_id, decision.decision)
    if not success:
        raise HTTPException(status_code=404, detail="Approval request not found")
    return {"status": "success", "request_id": request_id, "decision": decision.decision}

@router.get("/approvals")
def list_approvals():
    manager = ApprovalManager()
    return [
        {
            "id": item["task_id"],
            "status": item["status"].value,
            "diff": item.get("diff", ""),
            "risk_score": item.get("risk_score", 0.0),
            "impact": item.get("impact", "LOW"),
            "timestamp": item.get("requested_at"),
            "decision_at": item.get("decision_at"),
            "reason": item.get("reason"),
        }
        for item in manager.get_pending_approvals()
    ]

@router.post("/queue/actions/{action_id}/approve")
def approve_queue_action(action_id: int, request: Request):
    """Explicit operator approval for one durable SafeActionQueue action."""
    queue = SafeActionQueue()
    action = queue.get_action(action_id)
    if action is None:
        raise HTTPException(status_code=404, detail="Queue action not found")
    if action.get("status") != "QUEUED":
        raise HTTPException(status_code=409, detail=f"Queue action is {action.get('status')}, not QUEUED")
    principal = getattr(request.state, "dgm_principal", {}) or {}
    operator = str(principal.get("subject") or "local-operator")
    if not queue.approve(action_id, operator=operator):
        raise HTTPException(status_code=409, detail="Queue action was already decided or is no longer QUEUED")
    updated = queue.get_action(action_id)
    if not updated or updated.get("status") != "APPROVED" or not updated.get("is_approved"):
        raise HTTPException(status_code=503, detail="Queue approval could not be persisted")
    return {"status": "approved", "action_id": action_id, "approved_by": operator}


@router.post("/queue/actions/{action_id}/reject")
def reject_queue_action(action_id: int, rejection: QueueRejection, request: Request):
    """Explicit operator rejection for one durable SafeActionQueue action."""
    queue = SafeActionQueue()
    action = queue.get_action(action_id)
    if action is None:
        raise HTTPException(status_code=404, detail="Queue action not found")
    if action.get("status") != "QUEUED":
        raise HTTPException(status_code=409, detail=f"Queue action is {action.get('status')}, not QUEUED")
    principal = getattr(request.state, "dgm_principal", {}) or {}
    operator = str(principal.get("subject") or "local-operator")
    if not queue.reject(action_id, reason=rejection.reason.strip(), operator=operator):
        raise HTTPException(status_code=409, detail="Queue action was already decided or is no longer QUEUED")
    updated = queue.get_action(action_id)
    if not updated or updated.get("status") != "REJECTED":
        raise HTTPException(status_code=503, detail="Queue rejection could not be persisted")
    mission_id = (action.get("payload") or {}).get("mission_id")
    if action.get("action_type") == "MISSION_EXECUTION" and isinstance(mission_id, str) and mission_id:
        # Queue state and mission checkpoints are separate durable stores. Refresh
        # the checkpoint so a stale API cache cannot overwrite a terminal mission.
        mission = mission_engine._reload_mission_checkpoint(mission_id)
        if mission and mission.status not in {MissionStatus.COMPLETED, MissionStatus.CANCELLED, MissionStatus.FAILED}:
            queue_rejection = {
                "action_id": action_id,
                "operator": operator,
                "reason": rejection.reason.strip(),
            }
            mission.metadata["queue_rejection"] = queue_rejection
            mission_engine._update_status(
                mission,
                MissionStatus.CANCELLED,
                {
                    "error": "Mission rejected by operator: " + rejection.reason.strip(),
                    "queue_rejection": queue_rejection,
                },
            )
    return {"status": "rejected", "action_id": action_id, "mission_id": mission_id, "rejected_by": operator, "reason": rejection.reason.strip()}


@router.get("/queue")
def get_queue_status():
    """Requirement 5: Add queue inspection endpoint."""
    queue = SafeActionQueue()
    return {
        "health": queue.get_health(),
        "recent_actions": queue.list_all(limit=20)
    }
