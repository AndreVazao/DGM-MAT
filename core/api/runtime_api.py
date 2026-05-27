import json
from fastapi import APIRouter, HTTPException
from core.storage.storage_manager import storage_manager
from core.repository_cognition.repo_scanner import CognitiveRepoScanner

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
    # Placeholder: In real operation, we'd query KnowledgeEngine
    return {
        "total_memories": 154,
        "consolidated": 12,
        "patterns_detected": 5
    }
