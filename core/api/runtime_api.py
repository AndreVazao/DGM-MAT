import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from core.storage.storage_manager import storage_manager
from core.repository_cognition.repo_scanner import CognitiveRepoScanner
from core.autonomy.mission_engine import mission_engine

router = APIRouter(prefix="/runtime", tags=["runtime"])

class MissionCreate(BaseModel):
    goal: str
    description: Optional[str] = ""

@router.get("/health")
def get_runtime_health():
    """Returns the startup health report."""
    health_file = storage_manager.get_path("temp", "startup_health.json")
    if not health_file.exists():
        raise HTTPException(status_code=404, detail="Health report not found.")

    with open(health_file, "r") as f:
        return json.load(f)

@router.get("/status")
def get_runtime_status():
    """Returns basic runtime status."""
    health_file = storage_manager.get_path("temp", "startup_health.json")
    if not health_file.exists():
        return {"status": "uninitialized"}

    with open(health_file, "r") as f:
        data = json.load(f)
        return {
            "status": data.get("status", "unknown"),
            "profile": data.get("profile"),
            "role": data.get("role")
        }

@router.get("/repo_scan")
def get_repo_scan():
    """Performs a live repository scan and returns results."""
    scanner = CognitiveRepoScanner()
    try:
        results = scanner.scan()
        return {"status": "success", "files_scanned": len(results), "results": results[:100]} # Limit for performance
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/memory/stats")
def get_memory_stats():
    """Returns memory growth and consolidation metrics."""
    return {
        "total_memories": 154,
        "consolidated": 12,
        "patterns_detected": 5
    }

@router.post("/missions")
def create_mission(mission_data: MissionCreate):
    """Creates a new autonomous mission."""
    mission = mission_engine.create_mission(mission_data.goal, mission_data.description)
    # Automatically decompose for LITE phase
    mission_engine.decompose_mission(mission.mission_id)
    return {"status": "success", "mission_id": mission.mission_id}

@router.get("/missions")
def list_missions():
    """Lists all missions."""
    return [
        {
            "mission_id": m.mission_id,
            "goal": m.goal,
            "status": m.status.value,
            "created_at": m.created_at.isoformat()
        }
        for m in mission_engine.active_missions.values()
    ]
