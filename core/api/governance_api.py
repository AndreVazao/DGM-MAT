from __future__ import annotations

import hmac
import os
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


def _configured_governance_tokens() -> tuple[str, str]:
    """Return distinct server-configured credentials for privileged governance roles."""
    ceo_token = os.getenv("DGM_GOVERNANCE_CEO_TOKEN", "")
    owner_token = os.getenv("DGM_GOVERNANCE_OWNER_TOKEN", "")
    if (
        len(ceo_token) < 32
        or len(owner_token) < 32
        or hmac.compare_digest(ceo_token.encode("utf-8"), owner_token.encode("utf-8"))
    ):
        raise HTTPException(
            status_code=503,
            detail="Privileged governance is disabled until distinct CEO and owner credentials are configured.",
        )
    return ceo_token, owner_token


def _governance_credential_role(request: Request, *, required: bool = False) -> str | None:
    """Verify a separate privileged credential; never infer role from client labels or session IDs."""
    supplied = request.headers.get("x-dgm-governance-credential", "")
    if not supplied and not required:
        return None
    ceo_token, owner_token = _configured_governance_tokens()
    if supplied and hmac.compare_digest(supplied.encode("utf-8"), ceo_token.encode("utf-8")):
        return "ceo"
    if supplied and hmac.compare_digest(supplied.encode("utf-8"), owner_token.encode("utf-8")):
        return "owner"
    if required:
        raise HTTPException(status_code=403, detail="A valid privileged governance credential is required.")
    return None


def _require_governance_role(request: Request, role: str) -> None:
    if _governance_credential_role(request, required=True) != role:
        raise HTTPException(status_code=403, detail=f"Only the configured {role} credential may perform this action.")


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


@router.get("/approvals/pending")
def list_pending_governance_approvals():
    """Read durable approval requests for the PC/mobile cockpit; does not deliver or approve them."""
    try:
        return {"approvals": _meeting_registry().list_pending_approvals()}
    except RuntimeError as exc:
        raise _meeting_http_error(exc) from exc


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
        # Privileged role comes only from a distinct server-configured credential.
        role = _governance_credential_role(request)
        actor = "CEO" if role == "ceo" else str(principal.get("subject") or principal.get("session_id") or "")
        if not actor:
            raise HTTPException(status_code=401, detail="Authenticated actor identity is unavailable.")
        values = payload.model_dump()
        values["actor"] = actor
        return _meeting_registry().record_decision(meeting_id, **values)
    except (KeyError, ValueError, RuntimeError) as exc:
        raise _meeting_http_error(exc) from exc



@router.post("/meetings/{meeting_id}/owner-approval")
def approve_governance_meeting_as_owner(meeting_id: str, payload: MeetingApprovalRequest, request: Request):
    """Human final gate for critical structural changes; approval is not direct execution."""
    try:
        _require_governance_role(request, "owner")
        values = payload.model_dump()
        values["actor"] = "André"
        return _meeting_registry().approve_by_owner(meeting_id, **values)
    except (KeyError, ValueError, RuntimeError) as exc:
        raise _meeting_http_error(exc) from exc


@router.post("/meetings/{meeting_id}/approval")
def approve_governance_meeting(meeting_id: str, payload: MeetingApprovalRequest, request: Request):
    try:
        _require_governance_role(request, "ceo")
        values = payload.model_dump()
        values["actor"] = "CEO"
        return _meeting_registry().approve_decision(meeting_id, **values)
    except (KeyError, ValueError, RuntimeError) as exc:
        raise _meeting_http_error(exc) from exc



# Progressive trust: feedback is evidence, while delegation remains owner-controlled.
from core.governance.progressive_trust import ProgressiveTrustRegistry


class TrustFeedbackRequest(BaseModel):
    category: str = Field(min_length=1, max_length=200)
    scope: str = Field(min_length=1, max_length=200)
    outcome: str
    rationale: str = Field(min_length=1, max_length=2000)
    risk: str
    reversible: bool
    verified_success: bool = False

    model_config = ConfigDict(extra="forbid")


class TrustDelegationRequest(BaseModel):
    category: str = Field(min_length=1, max_length=200)
    scope: str = Field(min_length=1, max_length=200)
    max_risk: str
    min_verified_successes: int = Field(default=3, ge=3, le=20)
    rationale: str = Field(min_length=1, max_length=2000)

    model_config = ConfigDict(extra="forbid")


class TrustRevocationRequest(BaseModel):
    rationale: str = Field(min_length=1, max_length=2000)

    model_config = ConfigDict(extra="forbid")


class TrustEvaluationRequest(BaseModel):
    category: str = Field(min_length=1, max_length=200)
    scope: str = Field(min_length=1, max_length=200)
    risk: str
    protected_boundaries: list[str] = Field(default_factory=list, max_length=30)
    materially_changed: bool = False

    model_config = ConfigDict(extra="forbid")


def _trust_owner_actor(request: Request) -> str:
    _require_governance_role(request, "owner")
    return "André"


def _trust_error(exc: Exception) -> HTTPException:
    if isinstance(exc, KeyError):
        return HTTPException(status_code=404, detail="Trust delegation not found.")
    if isinstance(exc, ValueError):
        return HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, RuntimeError):
        return HTTPException(status_code=503, detail=str(exc))
    raise exc


@router.post("/trust/feedback")
def record_progressive_trust_feedback(payload: TrustFeedbackRequest, request: Request):
    """Record owner-attributed decision feedback; only verified outcomes count as successes."""
    try:
        actor = _trust_owner_actor(request)
        return ProgressiveTrustRegistry().record_feedback(actor=actor, **payload.model_dump())
    except (KeyError, ValueError, RuntimeError) as exc:
        raise _trust_error(exc) from exc


@router.post("/trust/delegations")
def grant_progressive_trust_delegation(payload: TrustDelegationRequest, request: Request):
    """Explicitly delegate a narrow low/medium-risk decision category; never execute actions."""
    try:
        actor = _trust_owner_actor(request)
        return ProgressiveTrustRegistry().grant_delegation(actor=actor, **payload.model_dump())
    except (KeyError, ValueError, RuntimeError) as exc:
        raise _trust_error(exc) from exc


@router.post("/trust/delegations/{delegation_id}/revoke")
def revoke_progressive_trust_delegation(delegation_id: str, payload: TrustRevocationRequest, request: Request):
    try:
        actor = _trust_owner_actor(request)
        return ProgressiveTrustRegistry().revoke_delegation(
            actor=actor, delegation_id=delegation_id, rationale=payload.rationale
        )
    except (KeyError, ValueError, RuntimeError) as exc:
        raise _trust_error(exc) from exc


@router.post("/trust/evaluate")
def evaluate_progressive_trust(payload: TrustEvaluationRequest):
    """Read-only policy check; an allowed decision does not grant execution permission."""
    try:
        return ProgressiveTrustRegistry().evaluate(**payload.model_dump())
    except (KeyError, ValueError, RuntimeError) as exc:
        raise _trust_error(exc) from exc
