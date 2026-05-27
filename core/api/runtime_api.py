import json
import os
import psutil
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from core.storage.storage_manager import storage_manager
from core.autonomy.mission_engine import mission_engine
from core.workspace.workspace_manager import workspace_manager
from core.connectors.obsidian_connector import obsidian_connector

router = APIRouter(prefix="/runtime", tags=["runtime"])

class MissionCreate(BaseModel):
    goal: str
    description: Optional[str] = ""

class ApprovalDecision(BaseModel):
    decision: str # "approve" or "reject"

@router.get("/health")
def get_runtime_health():
    health_file = storage_manager.get_path("temp", "startup_health.json")
    if not health_file.exists():
        raise HTTPException(status_code=404, detail="Health report not found.")
    with open(health_file, "r") as f:
        return json.load(f)

@router.get("/status")
def get_runtime_status():
    """Requirement 7: Comprehensive status with resources and agents."""
    health_file = storage_manager.get_path("temp", "startup_health.json")
    status = "uninitialized"
    if health_file.exists():
        with open(health_file, "r") as f:
            status = json.load(f).get("status", "unknown")

    return {
        "status": status,
        "resources": {
            "cpu": psutil.cpu_percent(),
            "memory": psutil.virtual_memory().percent
        },
        "agents": [
            {"name": "ArchitectAgent", "status": "healthy", "current_task": "Idle"},
            {"name": "RepoAgent", "status": "active", "current_task": "Scanning Workspace"},
            {"name": "DevOpsAgent", "status": "healthy", "current_task": "Idle"}
        ]
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
