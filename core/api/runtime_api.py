import json
import os
import psutil
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from core.storage.storage_manager import storage_manager
from core.repository_cognition.repo_scanner import CognitiveRepoScanner
from core.autonomy.mission_engine import mission_engine
from core.workspace.workspace_manager import workspace_manager
from core.connectors.obsidian_connector import obsidian_connector
from core.runtime.runtime_state_store import state_store

router = APIRouter(prefix="/runtime", tags=["runtime"])

class MissionCreate(BaseModel):
    goal: str
    description: Optional[str] = ""

class ApprovalDecision(BaseModel):
    decision: str # "approve" or "reject"

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
        "status": truth.status,
        "is_degraded": truth.is_degraded,
        "resources": {
            "cpu": psutil.cpu_percent(),
            "memory": psutil.virtual_memory().percent
        },
        "agents": truth.agents,
        "missions_active": len(truth.missions)
    }

@router.get("/truth")
def get_runtime_truth():
    """Requirement 4: Expose single source of truth."""
    return state_store.to_dict()

@router.get("/reality")
def get_runtime_reality():
    """Requirement 4: Expose observed reality."""
    return state_store.get_snapshot().reality

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
    mission = mission_engine.create_mission(mission_data.goal, mission_data.description)
    mission_engine.decompose_mission(mission.mission_id)
    return {"status": "success", "mission_id": mission.mission_id}

@router.get("/missions")
def list_missions():
    return [
        {
            "mission_id": m.mission_id,
            "goal": m.goal,
            "status": m.status.value,
            "created_at": getattr(m, 'created_at', None).isoformat() if hasattr(m, 'created_at') and m.created_at else None
        }
        for m in mission_engine.active_missions.values()
    ]

@router.post("/approvals/{request_id}")
def judge_approval(request_id: str, decision: ApprovalDecision):
    """Requirement 7: Functional approval/reject workflow."""
    success = mission_engine.handle_approval_decision(request_id, decision.decision)
    if not success:
        raise HTTPException(status_code=404, detail="Approval request not found")
    return {"status": "success", "request_id": request_id, "decision": decision.decision}

@router.get("/approvals")
def list_approvals():
    return [
        {"id": rid, "description": app["description"], "timestamp": app["timestamp"]}
        for rid, app in mission_engine.pending_approvals.items()
    ]
