from __future__ import annotations

from fastapi import APIRouter, HTTPException

from core.api.repository_learning_api import repository_learning_service
from core.conversation_intelligence.telescope_archive_importer import TelescopeArchiveImporter

router = APIRouter(prefix="/runtime/conversations", tags=["conversation-archive"])
telescope_archive_importer = TelescopeArchiveImporter()


@router.get("/telescope/status")
def telescope_archive_status():
    """Return import coverage only; never return transcript content."""
    return telescope_archive_importer.get_status()


@router.post("/telescope/import")
def import_telescope_conversations():
    """Import the operator-approved Telescope export, preserving user/assistant roles."""
    try:
        repositories = repository_learning_service.list_repositories(200)
        return telescope_archive_importer.import_latest(repositories=repositories)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
