"""Read-only operator API for recovery progress and source inventory."""
from __future__ import annotations

import json
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
            report = import_chatgpt_conversations_json(
                staged_path, archive_root, ledger, original_location="api-upload"
            )
        else:
            report = import_chatgpt_export_zip(
                staged_path, archive_root, ledger, original_location="api-upload"
            )

        return {
            "status": "completed" if report.failed == 0 else "completed_with_errors",
            "provider": "chatgpt",
            "format": normalized_format,
            "source_file": "uploaded-request-body",
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


MAX_RECOVERY_SEARCH_SOURCES = 500
MAX_RECOVERY_SEARCH_BYTES = 32 * 1024 * 1024
MAX_RECOVERY_SEARCH_FILE_BYTES = 4 * 1024 * 1024


def _message_text(value):
    """Extract searchable text from ChatGPT message content without changing the archive."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        chunks = []
        for child in value.values():
            chunks.extend(_message_text(child))
        return chunks
    if isinstance(value, list):
        chunks = []
        for child in value:
            chunks.extend(_message_text(child))
        return chunks
    return []


def _chatgpt_messages_path(source, *, verify_archive: bool = True) -> Path:
    archive = Path(source.raw_archive_path).expanduser().resolve()
    archive_root = Path(
        os.getenv("DGM_RECOVERY_ARCHIVE_ROOT", str(Path.home() / ".dgm-mat" / "recovery-archive"))
    ).expanduser().resolve()
    provider_root = (archive_root / source.provider).resolve()
    if source.provider != "chatgpt" or not archive.is_relative_to(provider_root):
        raise HTTPException(status_code=404, detail="Recovery archive is unavailable")
    if not archive.is_file():
        raise HTTPException(status_code=404, detail="Archived conversation is unavailable")
    if verify_archive and source.raw_sha256 and RecoveryLedger.sha256_file(archive).casefold() != source.raw_sha256.casefold():
        raise HTTPException(status_code=409, detail="Archived conversation failed integrity verification")
    suffix = ".conversation.json"
    if not archive.name.endswith(suffix):
        raise HTTPException(status_code=404, detail="Unsupported archive format")
    messages = archive.with_name(archive.name[:-len(suffix)] + ".messages.jsonl")
    if not messages.is_file() or not messages.resolve().is_relative_to(provider_root):
        raise HTTPException(status_code=404, detail="Message index is unavailable")
    return messages


@router.get("/search")
def search_recovery_sources(
    q: str = Query(min_length=2, max_length=200),
    provider: str | None = Query(default=None, min_length=2, max_length=40),
    limit: int = Query(default=25, ge=1, le=50),
):
    """Search imported conversation metadata and indexed message text, with hard scan bounds."""
    query = q.strip()
    if len(query) < 2:
        raise HTTPException(status_code=422, detail="q must contain at least two non-space characters")
    ledger = get_recovery_ledger()
    try:
        metadata = ledger.search_sources(query, provider=provider, limit=limit, offset=0)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    results = []
    seen = set()
    for source in metadata:
        key = (source.provider, source.source_id)
        seen.add(key)
        results.append({
            "provider": source.provider,
            "source_id": source.source_id,
            "title": source.title,
            "source_date": source.source_date,
            "match_type": "metadata",
            "snippet": source.title[:240],
        })

    scanned_sources = 0
    scanned_bytes = 0
    truncated = False
    candidates = ledger.list_sources(limit=MAX_RECOVERY_SEARCH_SOURCES, offset=0)
    needle = query.casefold()
    for source in candidates:
        if provider and source.provider.casefold() != provider.strip().casefold():
            continue
        if len(results) >= limit or scanned_sources >= MAX_RECOVERY_SEARCH_SOURCES:
            truncated = True
            break
        if source.provider != "chatgpt" or not source.raw_archive_path:
            continue
        try:
            messages_path = _chatgpt_messages_path(source, verify_archive=False)
            size = messages_path.stat().st_size
            if size > MAX_RECOVERY_SEARCH_FILE_BYTES or scanned_bytes + size > MAX_RECOVERY_SEARCH_BYTES:
                truncated = True
                continue
            scanned_sources += 1
            with messages_path.open("r", encoding="utf-8") as stream:
                for line in stream:
                    scanned_bytes += len(line.encode("utf-8"))
                    if scanned_bytes > MAX_RECOVERY_SEARCH_BYTES:
                        truncated = True
                        break
                    try:
                        record = json.loads(line)
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        continue
                    message = record.get("message") if isinstance(record, dict) else None
                    content = message.get("content") if isinstance(message, dict) else None
                    text_parts = _message_text(content)
                    joined = " ".join(text_parts)
                    position = joined.casefold().find(needle)
                    if position < 0:
                        continue
                    key = (source.provider, source.source_id)
                    if key not in seen:
                        start = max(0, position - 100)
                        snippet = joined[start:position + len(query) + 180]
                        results.append({
                            "provider": source.provider,
                            "source_id": source.source_id,
                            "title": source.title,
                            "source_date": source.source_date,
                            "match_type": "message",
                            "message_role": record.get("role", "unknown"),
                            "node_id": record.get("node_id", ""),
                            "snippet": snippet,
                        })
                        seen.add(key)
                    if len(results) >= limit:
                        truncated = True
                        break
            if truncated and scanned_bytes >= MAX_RECOVERY_SEARCH_BYTES:
                break
        except (OSError, HTTPException, ValueError):
            # One damaged or unavailable archive must not abort the whole search.
            continue

    return {
        "query": query,
        "provider_filter": provider,
        "limit": limit,
        "results": results[:limit],
        "result_count": min(len(results), limit),
        "scanned_sources": scanned_sources,
        "scanned_bytes": scanned_bytes,
        "truncated": truncated,
        "provider_access_used": False,
        "source_modified": False,
    }


@router.get("/sources/{provider}/{source_id}/messages")
def read_recovery_messages(
    provider: str,
    source_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """Read a bounded page of original archived messages after SHA-256 verification."""
    if len(provider) > 40 or len(source_id) > 160 or not provider.strip() or not source_id.strip():
        raise HTTPException(status_code=400, detail="Invalid recovery source identity")
    ledger = get_recovery_ledger()
    source = ledger.get(provider.strip().casefold(), source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Recovery source not found")
    messages_path = _chatgpt_messages_path(source)
    if messages_path.stat().st_size > MAX_RECOVERY_SEARCH_FILE_BYTES * 8:
        raise HTTPException(status_code=413, detail="Message index exceeds the read limit")
    items = []
    total = 0
    with messages_path.open("r", encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            if total >= offset and len(items) < limit:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                message = record.get("message") if isinstance(record, dict) else None
                items.append({
                    "node_id": record.get("node_id", ""),
                    "parent": record.get("parent"),
                    "children": record.get("children", []),
                    "timestamp": record.get("timestamp"),
                    "role": record.get("role", "unknown"),
                    "content": message.get("content") if isinstance(message, dict) else None,
                })
            total += 1
    return {
        "provider": source.provider,
        "source_id": source.source_id,
        "title": source.title,
        "total_messages": total,
        "limit": limit,
        "offset": offset,
        "items": items,
        "archive_sha256_verified": bool(source.raw_sha256),
        "provider_access_used": False,
        "source_modified": False,
    }
