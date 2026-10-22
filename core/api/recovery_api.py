"""Read-only operator API for recovery progress and source inventory."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, Query

from core.recovery.recovery_ledger import RecoveryLedger

router = APIRouter(prefix="/recovery", tags=["recovery"])


@lru_cache(maxsize=1)
def get_recovery_ledger() -> RecoveryLedger:
    configured = os.getenv("DGM_RECOVERY_LEDGER_PATH", "").strip()
    path = Path(configured).expanduser() if configured else Path.home() / ".dgm-mat" / "recovery-ledger.sqlite3"
    return RecoveryLedger(path)


@router.get("/status")
def recovery_status():
    """Return aggregate progress only; never inspect provider accounts or delete data."""
    ledger = get_recovery_ledger()
    sources = ledger.list_sources()
    counts: dict[str, int] = {}
    for source in sources:
        counts[source.capture_status] = counts.get(source.capture_status, 0) + 1
    return {
        "status": "available",
        "component": "recovery-ledger",
        "source_count": len(sources),
        "capture_status_counts": counts,
        "provider_connectors_enabled": False,
        "provider_deletion_enabled": False,
        "integration_status": "ledger_only",
    }


@router.get("/sources")
def list_recovery_sources(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """List registered source metadata without returning transcript contents."""
    sources = get_recovery_ledger().list_sources()
    page = sources[offset:offset + limit]
    return {
        "total": len(sources),
        "limit": limit,
        "offset": offset,
        "items": [
            {
                "provider": item.provider,
                "source_id": item.source_id,
                "title": item.title,
                "source_date": item.source_date,
                "source_url": item.source_url,
                "original_location": item.original_location,
                "project_key": item.project_key,
                "capture_status": item.capture_status,
                "completeness": item.completeness,
                "raw_archive_path": item.raw_archive_path,
                "raw_sha256": item.raw_sha256,
                "index_status": item.index_status,
                "repo_status": item.repo_status,
                "tree_revision": item.tree_revision,
                "deletion_status": item.deletion_status,
                "last_error": item.last_error,
                "attempts": item.attempts,
            }
            for item in page
        ],
    }
