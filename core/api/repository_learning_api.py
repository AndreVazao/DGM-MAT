"""Read-only status and operator controls for progressive repository learning."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from core.autonomy.repository_learning import RepositoryLearningService

router = APIRouter(prefix="/runtime/repository-learning", tags=["repository-learning"])
repository_learning_service = RepositoryLearningService()


@router.get("")
def repository_learning_status(limit: int = Query(default=200, ge=1, le=200)):
    """Return durable scan progress, repository metadata and evidence-based group suggestions."""
    status = repository_learning_service.get_status()
    repositories = repository_learning_service.list_repositories(limit)
    groups: dict[str, dict] = {}
    for repository in repositories:
        key = str(repository["project_group_id"])
        group = groups.setdefault(key, {
            "id": key,
            "name": repository["project_group"],
            "basis": repository["project_group_basis"],
            "confidence": repository["project_group_confidence"],
            "repositories": [],
        })
        group["repositories"].append(repository["name"])
        if repository["project_group_confidence"] < group["confidence"]:
            group["confidence"] = repository["project_group_confidence"]
    status["repositories"] = repositories
    status["project_groups"] = sorted(groups.values(), key=lambda item: item["name"].casefold())
    return status


@router.get("/tree")
def repository_tree(repo_path: str = Query(min_length=1, max_length=1024)):
    """Return a bounded tree artifact for a repository already in the inventory."""
    try:
        return repository_learning_service.read_tree(repo_path)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Repository tree not found") from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Repository tree artifact is missing") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


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
