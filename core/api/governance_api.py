from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from core.repository_intelligence.portfolio_auditor import RepositoryAuditEngine
from core.self_healing.self_repair_engine import SelfRepairEngine
from core.governance.runtime_capability_profile import collect_runtime_capability_profile
from core.operations.command_executor import CommandDenied, CommandExecutor
from core.operations.operation_audit import AuditWriteError, append_command_audit
from core.governance.meeting_registry import GovernanceMeetingRegistry


router = APIRouter(prefix="/governance", tags=["governance"])


class AuditRequest(BaseModel):
    limit: Optional[int] = None


class RepairRequest(BaseModel):
    confirm: bool = False
    dry_run: bool = True


@router.get("/runtime-capabilities")
def runtime_capabilities():
    """Expose a cheap, read-only profile of the current host's observed capacity."""
    return collect_runtime_capability_profile().to_dict()


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


class CommandRunRequest(BaseModel):
    command_id: str = Field(min_length=1, max_length=100)
    target_path: str | None = Field(default=None, max_length=4096)

    model_config = ConfigDict(extra="forbid")


@router.get("/commands/catalog")
def command_catalog():
    """List the explicit read-only command catalog; no execution occurs."""
    return CommandExecutor().catalog()


@router.post("/commands/run")
def run_governed_command(payload: CommandRunRequest, request: Request):
    """Run one allowlisted, read-only diagnostic with durable, redacted audit events."""
    principal = getattr(request.state, "dgm_principal", {}) or {}
    session_id = principal.get("session_id") if isinstance(principal, dict) else None

    # Persist the intent before execution. If the audit destination is unavailable,
    # do not run the command and leave an unaudited action behind.
    try:
        append_command_audit(
            event="command.requested",
            command_id=payload.command_id,
            status="requested",
            session_id=session_id,
        )
    except (AuditWriteError, ValueError):
        raise HTTPException(status_code=503, detail="Command audit storage is unavailable; execution refused.")

    try:
        result = CommandExecutor().execute(
            payload.command_id,
            target_path=payload.target_path,
        )
    except CommandDenied as exc:
        try:
            append_command_audit(
                event="command.denied",
                command_id=payload.command_id,
                status="denied",
                session_id=session_id,
            )
        except (AuditWriteError, ValueError):
            raise HTTPException(status_code=503, detail="Command denied; audit storage is unavailable.") from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        append_command_audit(
            event="command.completed",
            command_id=payload.command_id,
            status=str(result.get("status", "unknown")),
            session_id=session_id,
            duration_ms=result.get("duration_ms"),
            returncode=result.get("returncode"),
        )
    except (AuditWriteError, ValueError):
        raise HTTPException(
            status_code=503,
            detail="Command may have run, but its completion audit could not be persisted; verify before retrying.",
        )
    return result



# Central governance meetings: persistent records and approval gates.
class MeetingCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    meeting_type: str = Field(min_length=1, max_length=80)
    requested_by: str = Field(min_length=1, max_length=120)
    participants: list[str] = Field(min_length=1, max_length=50)
    agenda: list[str] = Field(min_length=1, max_length=30)
    proposal: str = Field(min_length=1, max_length=4000)
    related_departments: list[str] = Field(default_factory=list, max_length=30)

    model_config = ConfigDict(extra="forbid")


class MeetingContributionRequest(BaseModel):
    actor: str = Field(min_length=1, max_length=120)
    content: str = Field(min_length=1, max_length=4000)
    kind: str = "contribution"

    model_config = ConfigDict(extra="forbid")


class MeetingDecisionRequest(BaseModel):
    actor: str = Field(min_length=1, max_length=120)
    outcome: str
    rationale: str = Field(min_length=1, max_length=4000)
    action_plan: str = Field(default="", max_length=4000)

    model_config = ConfigDict(extra="forbid")


class MeetingApprovalRequest(BaseModel):
    actor: str = Field(min_length=1, max_length=120)
    approved: bool
    rationale: str = Field(min_length=1, max_length=4000)

    model_config = ConfigDict(extra="forbid")


def _meeting_registry() -> GovernanceMeetingRegistry:
    return GovernanceMeetingRegistry()


def _meeting_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, KeyError):
        return HTTPException(status_code=404, detail="Governance meeting not found.")
    if isinstance(exc, ValueError):
        return HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, RuntimeError):
        return HTTPException(status_code=503, detail=str(exc))
    raise exc


@router.get("/meetings")
def list_governance_meetings():
    try:
        return {"meetings": _meeting_registry().list_meetings()}
    except RuntimeError as exc:
        raise _meeting_http_error(exc) from exc


@router.post("/meetings")
def create_governance_meeting(payload: MeetingCreateRequest):
    try:
        return _meeting_registry().create_meeting(**payload.model_dump())
    except (ValueError, RuntimeError) as exc:
        raise _meeting_http_error(exc) from exc


@router.get("/meetings/{meeting_id}")
def get_governance_meeting(meeting_id: str):
    try:
        return _meeting_registry().get_meeting(meeting_id)
    except (KeyError, ValueError, RuntimeError) as exc:
        raise _meeting_http_error(exc) from exc


@router.post("/meetings/{meeting_id}/contributions")
def add_governance_meeting_contribution(meeting_id: str, payload: MeetingContributionRequest):
    try:
        return _meeting_registry().add_contribution(meeting_id, **payload.model_dump())
    except (KeyError, ValueError, RuntimeError) as exc:
        raise _meeting_http_error(exc) from exc


@router.post("/meetings/{meeting_id}/decision")
def decide_governance_meeting(meeting_id: str, payload: MeetingDecisionRequest, request: Request):
    try:
        principal = getattr(request.state, "dgm_principal", {}) or {}
        if not isinstance(principal, dict):
            raise HTTPException(status_code=401, detail="Authenticated principal is unavailable.")
        role = str(principal.get("governance_role") or principal.get("role") or "").casefold()
        # Never trust a client-supplied actor label to establish CEO authority.
        actor = "CEO" if role == "ceo" else str(principal.get("actor") or principal.get("username") or principal.get("session_id") or "")
        if not actor:
            raise HTTPException(status_code=401, detail="Authenticated actor identity is unavailable.")
        values = payload.model_dump()
        values["actor"] = actor
        return _meeting_registry().record_decision(meeting_id, **values)
    except (KeyError, ValueError, RuntimeError) as exc:
        raise _meeting_http_error(exc) from exc


@router.post("/meetings/{meeting_id}/approval")
def approve_governance_meeting(meeting_id: str, payload: MeetingApprovalRequest, request: Request):
    try:
        principal = getattr(request.state, "dgm_principal", {}) or {}
        if not isinstance(principal, dict):
            raise HTTPException(status_code=401, detail="Authenticated principal is unavailable.")
        role = str(principal.get("governance_role") or principal.get("role") or "").casefold()
        if role != "ceo":
            raise HTTPException(status_code=403, detail="Only an authenticated CEO principal may approve governance decisions.")
        values = payload.model_dump()
        values["actor"] = "CEO"
        return _meeting_registry().approve_decision(meeting_id, **values)
    except (KeyError, ValueError, RuntimeError) as exc:
        raise _meeting_http_error(exc) from exc
