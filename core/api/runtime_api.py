import json
from fastapi import APIRouter, HTTPException
from core.storage.storage_manager import storage_manager

router = APIRouter(prefix="/runtime", tags=["runtime"])

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
