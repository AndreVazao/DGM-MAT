"""Authenticated, local-only ingestion of visible browser conversation captures.

The endpoint receives rendered UI content from the DGM-MAT Chrome extension.
It never contacts providers, reads browser credentials, or modifies source accounts.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from urllib.parse import parse_qs, urlparse

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.recovery.recovery_ledger import RecoveryLedger, RecoverySource

router = APIRouter(prefix="/recovery/browser-capture", tags=["browser-conversation-capture"])

PROVIDER_HOSTS = {
    "chatgpt": {"chatgpt.com", "chat.openai.com"},
    "gemini": {"gemini.google.com"},
    "grok": {"grok.com", "x.com"},
}
MAX_DISCOVERY_ITEMS = 500
MAX_MESSAGES = 3000
MAX_MESSAGE_CHARS = 100_000
MAX_CAPTURE_BYTES = 20 * 1024 * 1024
SAFE_ID = re.compile(r"^[A-Za-z0-9._:-]{1,200}$")
PROPOSAL_MARKERS = re.compile(
    r"\b(i recommend|i suggest|i propose|we should|you should|recommendation|suggested approach|recomendo|sugiro|proponho|devemos|a minha recomendação|a solução proposta)\b",
    re.IGNORECASE,
)
CONFIRMATION_MARKERS = re.compile(
    r"\b(aprovo|aprovado|confirmo|autorizo|approved|i approve|confirmed|andré ok)\b",
    re.IGNORECASE,
)


def _knowledge_id(kind: str, provider: str, source_id: str, message_id: str = "") -> str:
    seed = "|".join((kind, provider, source_id, message_id))
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:32]


def _ledger() -> RecoveryLedger:
    configured = os.getenv("DGM_RECOVERY_LEDGER_PATH", "").strip()
    path = Path(configured).expanduser() if configured else Path.home() / ".dgm-mat" / "recovery-ledger.sqlite3"
    return RecoveryLedger(path)


def _archive_root() -> Path:
    configured = os.getenv("DGM_RECOVERY_ARCHIVE_ROOT", "").strip()
    root = Path(configured).expanduser() if configured else Path.home() / ".dgm-mat" / "recovery-archive"
    resolved = root.resolve()
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def _validate_provider_url(provider: str, value: str, source_id: str | None = None) -> str:
    if provider not in PROVIDER_HOSTS:
        raise ValueError("unsupported provider")
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower().rstrip(".")
    if parsed.scheme != "https" or host not in PROVIDER_HOSTS[provider]:
        raise ValueError("source URL is outside the provider allowlist")
    if parsed.username or parsed.password:
        raise ValueError("source URL must not contain credentials")
    if provider == "grok" and host == "x.com":
        if not (parsed.path == "/i/grok" or parsed.path.startswith("/i/grok/")):
            raise ValueError("x.com URL is not the Grok interface")
    if source_id is not None:
        if provider == "chatgpt":
            match = re.search(r"/c/([A-Za-z0-9_-]+)(?:/|$)", parsed.path)
        elif provider == "gemini":
            match = re.search(r"/app/([A-Za-z0-9_-]+)(?:/|$)", parsed.path)
        else:
            route_match = re.search(r"/(?:chat|c|i/grok)/([A-Za-z0-9_-]+)(?:/|$)", parsed.path)
            query_values = parse_qs(parsed.query)
            query_id = (query_values.get("conversation") or query_values.get("id") or [None])[0]
            candidate = route_match.group(1) if route_match else query_id
            if candidate != source_id:
                raise ValueError("source ID does not match the Grok conversation URL")
            return value
        if not match or match.group(1) != source_id:
            raise ValueError("source ID does not match the provider conversation URL")
    return value


class BrowserConversationItem(BaseModel):
    source_id: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=1, max_length=500)
    url: str = Field(min_length=12, max_length=2048)
    source_date: str = Field(default="unknown-date", max_length=80)

    model_config = ConfigDict(extra="forbid")

    @field_validator("source_id")
    @classmethod
    def validate_source_id(cls, value: str) -> str:
        if not SAFE_ID.fullmatch(value):
            raise ValueError("source_id contains unsupported characters")
        return value

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        return cleaned or "Untitled conversation"


class BrowserDiscoveryRequest(BaseModel):
    provider: Literal["chatgpt", "gemini", "grok"]
    items: list[BrowserConversationItem] = Field(min_length=1, max_length=MAX_DISCOVERY_ITEMS)

    model_config = ConfigDict(extra="forbid")


class BrowserMessage(BaseModel):
    message_id: str = Field(min_length=1, max_length=200)
    role: Literal["user", "assistant", "system", "tool", "model", "unknown"]
    content: str = Field(max_length=MAX_MESSAGE_CHARS)
    sequence: int = Field(ge=0, le=100_000)
    timestamp: str | None = Field(default=None, max_length=80)

    model_config = ConfigDict(extra="forbid")


class BrowserCaptureRequest(BaseModel):
    provider: Literal["chatgpt", "gemini", "grok"]
    source_id: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=1, max_length=500)
    url: str = Field(min_length=12, max_length=2048)
    messages: list[BrowserMessage] = Field(min_length=1, max_length=MAX_MESSAGES)
    truncated: bool = False
    history_start_reached: bool = False
    adapter_version: str = Field(default="0.1.0", max_length=40)
    captured_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    model_config = ConfigDict(extra="forbid")

    @field_validator("source_id")
    @classmethod
    def validate_source_id(cls, value: str) -> str:
        if not SAFE_ID.fullmatch(value):
            raise ValueError("source_id contains unsupported characters")
        return value


@router.get("/status")
def browser_capture_status():
    ledger = _ledger()
    return {
        "status": "available",
        "component": "authenticated-browser-capture",
        "source_count": ledger.source_count(),
        "capture_status_counts": ledger.status_counts(),
        "provider_access": "visible-ui-extension-only",
        "credential_store_access": False,
        "external_provider_api_calls": False,
        "full_history_completeness_claimed": False,
    }


@router.post("/discover")
def discover_browser_conversations(payload: BrowserDiscoveryRequest):
    ledger = _ledger()
    registered = 0
    rejected = 0
    errors: list[str] = []
    for item in payload.items:
        try:
            source_url = _validate_provider_url(payload.provider, item.url, item.source_id)
            ledger.register(RecoverySource(
                provider=payload.provider,
                source_id=item.source_id,
                title=item.title,
                source_date=item.source_date or "unknown-date",
                source_url=source_url,
                original_location="authenticated-chrome-visible-ui",
                capture_status="discovered",
            ))
            registered += 1
        except (ValueError, OSError) as exc:
            rejected += 1
            errors.append(type(exc).__name__ + ":" + item.source_id[:80])
    return {
        "status": "registered" if registered else "no_valid_sources",
        "provider": payload.provider,
        "discovered": len(payload.items),
        "registered": registered,
        "rejected": rejected,
        "errors": errors[:50],
    }


@router.post("/next")
def claim_next_browser_conversation():
    ledger = _ledger()
    source = ledger.next_source(pipeline="authenticated_browser_capture")
    if source is None:
        return {"status": "queue_empty", "next": None}
    return {
        "status": "claimed",
        "next": {
            "provider": source.provider,
            "source_id": source.source_id,
            "title": source.title,
            "url": source.source_url,
            "source_date": source.source_date,
            "attempt": source.attempts,
        },
    }


class BrowserCaptureBlockRequest(BaseModel):
    provider: Literal["chatgpt", "gemini", "grok"]
    source_id: str = Field(min_length=1, max_length=200)
    status: Literal["blocked", "rate_limited", "failed"] = "blocked"
    reason: str = Field(min_length=1, max_length=300)

    model_config = ConfigDict(extra="forbid")


@router.post("/block")
def mark_browser_conversation_blocked(payload: BrowserCaptureBlockRequest):
    ledger = _ledger()
    if ledger.get(payload.provider, payload.source_id) is None:
        raise HTTPException(status_code=404, detail="Conversation source was not discovered.")
    ledger.checkpoint(
        payload.provider,
        payload.source_id,
        capture_status=payload.status,
        completeness="unknown",
        detail=payload.reason,
        pipeline="authenticated_browser_capture",
    )
    return {
        "status": payload.status,
        "provider": payload.provider,
        "source_id": payload.source_id,
        "reason": payload.reason,
    }


@router.post("/capture")
def archive_browser_conversation(payload: BrowserCaptureRequest):
    try:
        source_url = _validate_provider_url(payload.provider, payload.url, payload.source_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    ledger = _ledger()
    source = ledger.get(payload.provider, payload.source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Conversation was not discovered before capture.")
    ordered = sorted(payload.messages, key=lambda item: (item.sequence, item.message_id))
    if len({item.message_id for item in ordered}) != len(ordered):
        raise HTTPException(status_code=422, detail="Duplicate message IDs in capture.")
    if len({item.sequence for item in ordered}) != len(ordered):
        raise HTTPException(status_code=422, detail="Duplicate message sequence numbers in capture.")

    record = {
        "schema_version": 1,
        "id": payload.source_id,
        "conversation_id": payload.source_id,
        "provider": payload.provider,
        "source_id": payload.source_id,
        "participants": [
            {"participant_id": "operator", "role": "user"},
            {"participant_id": payload.provider, "role": "assistant"},
        ],
        "title": " ".join(payload.title.split())[:500],
        "source_url": source_url,
        "source_date": source.source_date,
        "captured_at": payload.captured_at,
        "capture_method": "authenticated_visible_ui",
        "adapter_version": payload.adapter_version,
        "messages": [item.model_dump() for item in ordered],
        "message_count": len(ordered),
        "truncated": payload.truncated,
        "history_start_reached": payload.history_start_reached,
        # Hash integrity is distinct from proof that every historical message was rendered.
        "completeness": "visible_snapshot",
        "full_history_verified": False,
    }
    encoded = (json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    if len(encoded) > MAX_CAPTURE_BYTES:
        raise HTTPException(status_code=413, detail="Conversation capture exceeds the 20 MiB limit.")
    digest = hashlib.sha256(encoded).hexdigest()
    source_key = hashlib.sha256(payload.source_id.encode("utf-8")).hexdigest()[:32]
    folder = (_archive_root() / "browser-ui" / payload.provider / source_key).resolve()
    archive_root = (_archive_root() / "browser-ui" / payload.provider).resolve()
    if not folder.is_relative_to(archive_root):
        raise HTTPException(status_code=400, detail="Invalid archive destination.")
    folder.mkdir(parents=True, exist_ok=True)
    destination = folder / (digest + ".capture.json")
    if destination.is_symlink():
        raise HTTPException(status_code=400, detail="Symlink archive destinations are denied.")
    archive_reused = destination.exists() and source.raw_sha256 == digest
    if archive_reused and RecoveryLedger.sha256_file(destination) != digest:
        raise HTTPException(status_code=500, detail="Existing archive integrity verification failed.")
    if not destination.exists():
        descriptor = None
        try:
            descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "wb") as stream:
                descriptor = None
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
        except FileExistsError:
            pass
        except OSError as exc:
            if descriptor is not None:
                os.close(descriptor)
            destination.unlink(missing_ok=True)
            raise HTTPException(status_code=500, detail="Local conversation archive write failed.") from exc

    actual_digest = RecoveryLedger.sha256_file(destination)
    if actual_digest != digest:
        raise HTTPException(status_code=500, detail="Archive integrity verification failed.")

    index_status = "pending"
    index_summary: dict = {}
    normalized_destination = folder / (digest + ".normalized.json")
    try:
        from core.conversation_intelligence.pipeline import ConversationIntelligencePipeline
        from core.conversation_intelligence.telescope_archive_importer import redact_conversation_text
        from core.storage.storage_manager import storage_manager

        normalized_record = dict(record)
        normalized_record["title"] = redact_conversation_text(record["title"])
        normalized_record["messages"] = [
            {**message, "content": redact_conversation_text(message["content"])}
            for message in record["messages"]
        ]
        normalized_bytes = (
            json.dumps(normalized_record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\\n"
        ).encode("utf-8")
        if normalized_destination.is_symlink():
            raise OSError("normalized archive symlink is denied")
        if not normalized_destination.exists():
            descriptor = os.open(
                normalized_destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600
            )
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(normalized_bytes)
                stream.flush()
                os.fsync(stream.fileno())
        cognition = storage_manager.get_path("cognition") / "conversation_intelligence"
        pipeline = ConversationIntelligencePipeline(
            progress_store_path=cognition / "progress.sqlite3",
            knowledge_store_path=cognition / "knowledge.sqlite3",
        )
        audits = pipeline.ingest_file(normalized_destination, provider=payload.provider)
        index_summary = pipeline.summarize(audits)
        knowledge = pipeline.knowledge_store
        intent_ids: list[str] = []
        proposal_ids: list[str] = []
        intent_evidence: list[str] = []
        proposal_evidence: list[str] = []
        from core.conversation_intelligence.models import AIProposal, UserIntent

        for message in normalized_record["messages"]:
            role = str(message.get("role", "unknown")).casefold()
            message_id = str(message.get("message_id", ""))
            content = str(message.get("content", "")).strip()
            if not content or not message_id:
                continue
            evidence_ref = f"archive-sha256:{digest}#message:{message_id}"
            if role == "user":
                intent_id = _knowledge_id("intent", payload.provider, payload.source_id, message_id)
                knowledge.save_intent(UserIntent(
                    intent_id=intent_id,
                    statement=content,
                    status="unverified",
                    source_conversation_id=payload.source_id,
                    source_message_id=message_id,
                    observed_at=message.get("timestamp") or payload.captured_at,
                    evidence=[evidence_ref],
                    confidence=0.35,
                    reviewed_by_user=False,
                ))
                intent_ids.append(intent_id)
                intent_evidence.append(evidence_ref)
                if CONFIRMATION_MARKERS.search(content):
                    knowledge.create_review_task(
                        task_id=_knowledge_id("possible-confirmation-review", payload.provider, payload.source_id, message_id),
                        item_type="intent",
                        item_id=intent_id,
                        reason="Possible operator confirmation phrase; verify its context before recording a decision.",
                        evidence=[evidence_ref],
                    )
            elif role in {"assistant", "model"} and PROPOSAL_MARKERS.search(content):
                proposal_id = _knowledge_id("proposal", payload.provider, payload.source_id, message_id)
                knowledge.save_proposal(AIProposal(
                    proposal_id=proposal_id,
                    statement=content,
                    source_conversation_id=payload.source_id,
                    source_message_id=message_id,
                    accepted=None,
                    decision_id=None,
                ))
                proposal_ids.append(proposal_id)
                proposal_evidence.append(evidence_ref)

        if intent_ids:
            knowledge.create_review_task(
                task_id=_knowledge_id("intent-review", payload.provider, payload.source_id),
                item_type="intent",
                item_id=payload.source_id,
                reason="Review extracted operator requests and confirm project/owner attribution.",
                evidence=intent_evidence[:100],
            )
        if proposal_ids:
            knowledge.create_review_task(
                task_id=_knowledge_id("proposal-review", payload.provider, payload.source_id),
                item_type="proposal",
                item_id=payload.source_id,
                reason="Review AI-generated proposal candidates; acceptance has not been inferred.",
                evidence=proposal_evidence[:100],
            )

        suggested_project = next(
            (audit.suggested_project for audit in audits if audit.suggested_project),
            None,
        )
        if suggested_project:
            current_source = ledger.get(payload.provider, payload.source_id)
            if current_source:
                ledger.register(replace(current_source, project_key=str(suggested_project)[:200]))
        else:
            knowledge.create_review_task(
                task_id=_knowledge_id("project-attribution-review", payload.provider, payload.source_id),
                item_type="coverage",
                item_id=payload.source_id,
                reason="Project and owner attribution remain unknown; review conversation evidence.",
                evidence=[f"archive-sha256:{digest}"],
            )

        index_summary["knowledge"] = knowledge.summary()
        index_summary["intent_candidates"] = len(intent_ids)
        index_summary["proposal_candidates"] = len(proposal_ids)
        index_summary["suggested_project"] = suggested_project
        index_summary["confirmed_decisions_created"] = 0
        index_status = "indexed"
    except Exception as exc:
        # Archival integrity is independent from intelligence indexing. Keep the
        # raw capture and allow a later indexing retry; never lose a good archive.
        index_status = "failed"
        index_summary = {"error_type": type(exc).__name__}

    ledger.checkpoint(
        payload.provider,
        payload.source_id,
        capture_status="verified",
        completeness="visible_snapshot",
        raw_archive_path=str(destination),
        raw_sha256=digest,
        index_status=index_status,
        detail="visible UI snapshot archived; full history not independently verified",
        pipeline="authenticated_browser_capture",
    )
    return {
        "status": "already_archived" if archive_reused else "archived_and_hash_verified",
        "provider": payload.provider,
        "source_id": payload.source_id,
        "message_count": len(ordered),
        "sha256": digest,
        "archive_path": str(destination),
        "normalized_archive_path": str(normalized_destination) if normalized_destination.is_file() else None,
        "index_status": index_status,
        "index_summary": index_summary,
        "completeness": "visible_snapshot",
        "full_history_verified": False,
        "truncated": payload.truncated,
    }


@router.post("/retry")
def retry_browser_conversation(provider: Literal["chatgpt", "gemini", "grok"], source_id: str):
    try:
        _ledger().request_retry(provider, source_id, "operator_or_extension_retry")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Conversation source was not found.") from exc
    return {"status": "retry_queued", "provider": provider, "source_id": source_id}
