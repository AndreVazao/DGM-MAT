"""Read-only operator API for recovery progress and source inventory."""
from __future__ import annotations

import os
import tempfile
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, Request

from core.recovery.chatgpt_export_importer import (
    ChatGPTExportError,
    import_chatgpt_conversations_json,
    import_chatgpt_export_zip,
)
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
    counts = ledger.status_counts()
    return {
        "status": "available",
        "component": "recovery-ledger",
        "source_count": ledger.source_count(),
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
    ledger = get_recovery_ledger()
    total = ledger.source_count()
    page = ledger.list_sources(limit=limit, offset=offset)
    return {
        "total": total,
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


MAX_CHATGPT_UPLOAD_BYTES = 512 * 1024 * 1024


@router.post("/import/chatgpt")
async def import_chatgpt_export(request: Request, format: str = Query(default="zip")):
    """Import a user-supplied ChatGPT JSON/ZIP export into the local recovery archive.

    The request body is streamed to a private temporary file with a strict size cap.
    The original upload is never modified; ZIP extraction is delegated to the safe
    importer, which reads only the uniquely identified conversations.json member.
    """
    normalized_format = str(format).strip().casefold()
    if normalized_format not in {"json", "zip"}:
        raise HTTPException(status_code=400, detail="format must be 'json' or 'zip'")

    archive_root = Path(
        os.getenv("DGM_RECOVERY_ARCHIVE_ROOT", str(Path.home() / ".dgm-mat" / "recovery-archive"))
    ).expanduser().resolve()
    try:
        archive_root.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise HTTPException(status_code=500, detail="Recovery archive directory is unavailable") from exc

    suffix = ".json" if normalized_format == "json" else ".zip"
    staged_path: Path | None = None
    total_bytes = 0
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", prefix="dgm-chatgpt-upload-", suffix=suffix,
            dir=str(archive_root), delete=False,
        ) as staged:
            staged_path = Path(staged.name)
            async for chunk in request.stream():
                if not chunk:
                    continue
                total_bytes += len(chunk)
                if total_bytes > MAX_CHATGPT_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail="ChatGPT export exceeds the 512 MiB upload limit")
                staged.write(chunk)
            staged.flush()
            os.fsync(staged.fileno())

        if total_bytes == 0:
            raise HTTPException(status_code=400, detail="The uploaded export is empty")

        ledger = get_recovery_ledger()
        if normalized_format == "json":
            report = import_chatgpt_conversations_json(staged_path, archive_root, ledger)
        else:
            report = import_chatgpt_export_zip(staged_path, archive_root, ledger)

        return {
            "status": "completed" if report.failed == 0 else "completed_with_errors",
            "provider": "chatgpt",
            "format": normalized_format,
            "source_file": report.source_file,
            "discovered": report.discovered,
            "archived": report.archived,
            "skipped_existing": report.skipped_existing,
            "partial": report.partial,
            "failed": report.failed,
            "errors": list(report.errors[:50]),
            "error_count": len(report.errors),
            "source_count": ledger.source_count(),
            "provider_access_used": False,
            "source_modified": False,
            "provider_deletion_attempted": False,
        }
    except HTTPException:
        raise
    except (ChatGPTExportError, OSError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        if staged_path is not None:
            try:
                staged_path.unlink(missing_ok=True)
            except OSError:
                pass
