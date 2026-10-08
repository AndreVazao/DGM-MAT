from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.repository_intelligence.portfolio_auditor import RepositoryAuditEngine
from core.self_healing.self_repair_engine import SelfRepairEngine


router = APIRouter(prefix="/governance", tags=["governance"])


class AuditRequest(BaseModel):
    limit: Optional[int] = None


class RepairRequest(BaseModel):
    confirm: bool = False
    dry_run: bool = True


@router.get("/audit/workspace")
def audit_workspace(limit: Optional[int] = None):
    """Read-only evidence-first audit of the canonical workspace."""
    engine = RepositoryAuditEngine(Path("C:/ProgramasGodMode"))
    return engine.audit_workspace(limit=limit)


@router.get("/audit/self")
def audit_self():
    """Read-only audit of DGM-MAT itself."""
    return SelfRepairEngine().diagnose()


@router.get("/repair/self/plan")
def self_repair_plan():
    """Return a repair plan without mutating anything."""
    return SelfRepairEngine().diagnose()


@router.post("/repair/self/apply")
def apply_self_repair(request: RepairRequest):
    """Apply only explicitly safe, non-structural DGM-MAT repairs."""
    if not request.confirm:
        raise HTTPException(status_code=400, detail="Explicit confirm=true is required.")
    return SelfRepairEngine().apply_safe(dry_run=request.dry_run)
from core.conversation_intelligence import ConversationIntelligencePipeline, ConversationRecord

class ConversationRequest(BaseModel):
    conversation_id: str
    provider: str
    title: str
    content: str
    url: str | None = None

@router.post("/conversations/analyze")
def analyze_conversation(request: ConversationRequest):
    pipeline = ConversationIntelligencePipeline()
    conversation = ConversationRecord(request.conversation_id, request.provider, request.title, request.content, "dashboard", request.url)
    artifacts = pipeline.extractor.extract(conversation)
    audit = pipeline.auditor.audit(conversation, artifacts)
    return {
        "conversation": audit.conversation.__dict__,
        "artifacts": [a.__dict__ for a in audit.artifacts],
        "findings": [f.__dict__ for f in audit.findings],
        "suggested_project": audit.suggested_project,
        "suggested_title": audit.suggested_title,
    }
