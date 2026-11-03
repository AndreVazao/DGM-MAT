"""Read-only status and operator controls for progressive repository learning."""
from __future__ import annotations

from fastapi import APIRouter, Query

from core.autonomy.repository_learning import RepositoryLearningService

router = APIRouter(prefix="/runtime/repository-learning", tags=["repository-learning"])
repository_learning_service = RepositoryLearningService()


@router.get("")
def repository_learning_status(limit: int = Query(default=50, ge=1, le=200)):
    """Return durable scan progress and a bounded metadata-only repository index."""
    status = repository_learning_service.get_status()
    status["repositories"] = repository_learning_service.list_repositories(limit)
    return status


@router.post("/start")
def start_repository_learning():
    """Start or resume the incremental metadata-only repository worker."""
    started = repository_learning_service.start()
    return {
        "status": "started" if started else "already_running",
        "progress": repository_learning_service.get_status(),
    }


@router.post("/stop")
def stop_repository_learning():
    """Pause the worker without discarding its durable cursor or learned metadata."""
    repository_learning_service.stop()
    return {
        "status": "stopped",
        "progress": repository_learning_service.get_status(),
    }
