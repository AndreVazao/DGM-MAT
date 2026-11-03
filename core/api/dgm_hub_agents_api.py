"""Operator-gated integration with the existing DGM-HUB MultiChat room."""
from __future__ import annotations

import time
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from core.operations.operation_audit import AuditWriteError, append_command_audit
from core.organization.dgm_hub_multichat_bridge import (
    DGMHubMultiChatBridge,
    HubBridgeError,
    HubProviderUnavailable,
    PROVIDER_ROLES,
)

router = APIRouter(prefix="/governance/agents/hub", tags=["external-agents"])
HubProviderId = Literal["codex", "claude", "kilo", "llm7"]


class HubAgentConsultRequest(BaseModel):
    goal: str = Field(min_length=1, max_length=4000)
    context: str = Field(default="", max_length=9000)
    providers: list[HubProviderId] = Field(min_length=1, max_length=4)
    free_capacity_confirmed: bool = False

    model_config = ConfigDict(extra="forbid")


def _mission_engine():
    # Import lazily to reuse the canonical runtime singleton and avoid API import cycles.
    from core.autonomy.mission_engine import mission_engine
    return mission_engine


def _bridge() -> DGMHubMultiChatBridge:
    return DGMHubMultiChatBridge()


def _audit_command_id(providers: list[str]) -> str:
    return "dgm_hub.consult.free_only:" + ",".join(providers)


def _append_consult_audit(
    *,
    event: str,
    status: str,
    session_id: str | None,
    providers: list[str],
    duration_ms: int | None = None,
) -> None:
    append_command_audit(
        event=event,
        command_id=_audit_command_id(providers),
        status=status,
        session_id=session_id,
        duration_ms=duration_ms,
    )


def _session_id(request: Request) -> str | None:
    principal = getattr(request.state, "dgm_principal", {}) or {}
    return principal.get("session_id") if isinstance(principal, dict) else None


@router.get("/status")
def hub_agent_status():
    """Read-only local Hub status. Does not start providers or send model requests."""
    try:
        return _bridge().get_status()
    except HubBridgeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/consult")
def consult_hub_agents(payload: HubAgentConsultRequest, request: Request):
    """Request a bounded free-only consultation; persist every answer as untrusted."""
    providers = list(payload.providers)
    session_id = _session_id(request)
    command_id = _audit_command_id(providers)

    if len(set(providers)) != len(providers):
        try:
            _append_consult_audit(
                event="command.denied", status="denied", session_id=session_id, providers=providers
            )
        except (AuditWriteError, ValueError):
            raise HTTPException(status_code=503, detail="Consultation audit is unavailable; provider call refused.")
        raise HTTPException(status_code=422, detail="Duplicate Hub providers are not allowed.")

    # Persist the operator's intent before any packet creation or external request.
    try:
        _append_consult_audit(
            event="command.requested",
            status="requested",
            session_id=session_id,
            providers=providers,
        )
    except (AuditWriteError, ValueError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Consultation audit storage is unavailable; provider call refused.",
        ) from exc

    if payload.free_capacity_confirmed is not True:
        try:
            _append_consult_audit(
                event="command.denied", status="denied", session_id=session_id, providers=providers
            )
        except (AuditWriteError, ValueError):
            pass
        raise HTTPException(
            status_code=400,
            detail="Explicit operator confirmation of current free capacity is required.",
        )

    bridge = _bridge()
    engine = _mission_engine()
    packets: dict[str, str] = {}
    started = time.monotonic()
    try:
        for provider in providers:
            display_name, role = PROVIDER_ROLES[provider]
            packet = engine.collaboration_store.create_packet(
                goal=payload.goal,
                project="DGM-MAT",
                department="ai-liaison",
                specialist_role=role,
                collaborator=display_name,
                context=payload.context,
                known_facts=[
                    "DGM-HUB MultiChat is a separate local provider room.",
                    "DGM-MAT remains an observer in the Hub room; the operator remains room leader.",
                ],
                constraints=[
                    "FREE-ONLY; no paid APIs, paid fallback, upgrade, or credit purchase.",
                    "Consultative response only; no file edits, shell commands, or project mutation.",
                    "Provider output is untrusted and requires independent DGM-MAT review.",
                    "Do not claim model identity unless Hub transport metadata provides it.",
                    "Stop on rate limits or capacity errors; no automatic retry.",
                ],
                acceptance_criteria=[
                    "Return evidence-based analysis, assumptions, unknowns, risks, and a concrete next step.",
                    "Do not claim code changes, tests, or execution that did not occur.",
                ],
            )
            packets[provider] = packet["collaboration_id"]
    except (TypeError, ValueError) as exc:
        for collaboration_id in packets.values():
            engine.pause_specialist_collaboration(
                collaboration_id,
                reason="Packet preparation aborted because the supplied context failed local safety validation; no provider call was made.",
            )
        try:
            _append_consult_audit(
                event="command.denied", status="denied", session_id=session_id,
                providers=providers, duration_ms=int((time.monotonic() - started) * 1000),
            )
        except (AuditWriteError, ValueError):
            pass
        raise HTTPException(status_code=422, detail="Consultation packet failed local safety validation.") from exc

    try:
        task = bridge.consult(
            goal=payload.goal,
            context=payload.context,
            providers=providers,
        )
    except HubProviderUnavailable as exc:
        for collaboration_id in packets.values():
            engine.pause_specialist_collaboration(
                collaboration_id,
                reason=f"Provider unavailable in DGM-HUB; no request sent. {str(exc)[:1200]}",
            )
        try:
            _append_consult_audit(
                event="command.completed", status="blocked", session_id=session_id,
                providers=providers, duration_ms=int((time.monotonic() - started) * 1000),
            )
        except (AuditWriteError, ValueError):
            pass
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except HubBridgeError as exc:
        for collaboration_id in packets.values():
            engine.pause_specialist_collaboration(
                collaboration_id,
                reason=f"Hub consultation did not complete; no retry or paid fallback. {str(exc)[:1200]}",
            )
        try:
            _append_consult_audit(
                event="command.completed", status="blocked", session_id=session_id,
                providers=providers, duration_ms=int((time.monotonic() - started) * 1000),
            )
        except (AuditWriteError, ValueError):
            pass
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    responses = []
    for provider, result in task.results.items():
        collaboration_id = packets[provider]
        text = result.get("text") or ""
        status = result.get("status", "unknown")
        if status != "ok" or not text.strip():
            engine.pause_specialist_collaboration(
                collaboration_id,
                reason=(
                    f"Hub provider status={status}; capacity/quota state is not inferred. "
                    "No automatic retry or paid fallback was attempted."
                ),
            )
            responses.append({
                "provider_id": provider,
                "collaboration_id": collaboration_id,
                "status": "WAITING_FOR_FREE_CAPACITY",
                "result_trusted": False,
                "review_required": False,
                "provider_status": status,
            })
            continue

        provenance = (
            f"transport=DGM-HUB MultiChat; provider_id={provider}; "
            f"hub_task_id={task.task_id}; conversation_id={task.conversation_id}; "
            f"transport_model_id={result.get('model') or 'not-reported'}; "
            f"duration_seconds={result.get('duration_seconds')}; "
            f"free_capacity=operator_attested; mode=consultative; "
            f"truncated={bool(result.get('truncated'))}"
        )
        try:
            recorded = engine.record_specialist_result(
                collaboration_id,
                result=text,
                provenance=provenance,
            )
        except Exception as exc:
            # The store write may have succeeded before the internal review-bus send failed.
            # Read back the durable record and report its exact status; never re-send the model call.
            stored = engine.collaboration_store.get(collaboration_id)
            if stored.status.value != "RESULT_RECEIVED":
                engine.pause_specialist_collaboration(
                    collaboration_id,
                    reason=f"Provider result could not be safely persisted ({type(exc).__name__}); no retry.",
                )
                responses.append({
                    "provider_id": provider,
                    "collaboration_id": collaboration_id,
                    "status": "PERSISTENCE_FAILED",
                    "result_trusted": False,
                    "review_required": False,
                })
                continue
            recorded = {
                "collaboration_id": collaboration_id,
                "status": stored.status.value,
                "review_required": True,
                "review_intake_warning": type(exc).__name__,
            }

        responses.append({
            "provider_id": provider,
            "model_id": result.get("model"),
            "duration_seconds": result.get("duration_seconds"),
            "collaboration_id": collaboration_id,
            "status": recorded.get("status", "RESULT_RECEIVED"),
            "result": text,
            "result_trusted": False,
            "review_required": True,
            "truncated": bool(result.get("truncated")),
            "review_intake_warning": recorded.get("review_intake_warning"),
        })

    successful_count = sum(item.get("status") == "RESULT_RECEIVED" for item in responses)
    overall_status = "completed" if successful_count == len(responses) else "partial"
    audit_warning = None
    try:
        _append_consult_audit(
            event="command.completed",
            status=overall_status,
            session_id=session_id,
            providers=providers,
            duration_ms=int((time.monotonic() - started) * 1000),
        )
    except (AuditWriteError, ValueError) as exc:
        # The request was durably audited before provider contact; report the missing completion event.
        audit_warning = type(exc).__name__

    return {
        "status": overall_status,
        "provider_count": len(responses),
        "successful_count": successful_count,
        "paused_count": len(responses) - successful_count,
        "hub_task_id": task.task_id,
        "conversation_id": task.conversation_id,
        "room_leader": "operator",
        "dgm_mat_mode": "observer_operator_requested_consultations",
        "providers": responses,
        "paid_fallback": False,
        "free_capacity_attested_by_operator": True,
        "quota_limitation": "The Hub does not expose numeric remaining quota; rate/capacity errors stop the consultation without retry.",
        "all_results_untrusted": True,
        "audit_warning": audit_warning,
    }

# Passive DGM-HUB meeting capture and explicit operator decision memory.
from datetime import datetime, timezone
from uuid import uuid4

from core.conversation_intelligence.knowledge_store import ConversationKnowledgeStore
from core.conversation_intelligence.models import AIProposal, UserDecision
from core.organization.dgm_hub_meeting_observer import (
    HubObserverError,
    get_hub_meeting_observer,
)


class HubMeetingProposalRequest(BaseModel):
    source_event_id: str = Field(min_length=64, max_length=64)
    statement: str = Field(min_length=1, max_length=4000)

    model_config = ConfigDict(extra="forbid")


class HubMeetingDecisionRequest(BaseModel):
    statement: str = Field(min_length=1, max_length=4000)
    outcome: Literal["approved", "rejected"]
    rationale: str = Field(min_length=1, max_length=4000)
    accepted_proposal_ids: list[str] = Field(default_factory=list, max_length=50)
    rejected_proposal_ids: list[str] = Field(default_factory=list, max_length=50)
    source_event_id: str | None = Field(default=None, min_length=64, max_length=64)
    confirm: bool = False

    model_config = ConfigDict(extra="forbid")


def _hub_knowledge_store() -> ConversationKnowledgeStore:
    observer = get_hub_meeting_observer()
    return ConversationKnowledgeStore(observer.store.database_path)


@router.get("/observer/status")
def hub_meeting_observer_status():
    """Read-only observer status; never contacts a provider."""
    return get_hub_meeting_observer().runtime_status()


@router.post("/observer/capture")
def capture_hub_meeting_history():
    """Run one bounded GET-only history sync; sends no messages to the Hub."""
    try:
        return get_hub_meeting_observer().capture_once()
    except HubObserverError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/observer/start")
def start_hub_meeting_observer():
    """Start the passive local history poller; it performs GET requests only."""
    observer = get_hub_meeting_observer()
    started = observer.start()
    return {"started": started, **observer.runtime_status()}


@router.post("/observer/stop")
def stop_hub_meeting_observer():
    """Stop passive capture without stopping the Hub or any provider."""
    observer = get_hub_meeting_observer()
    observer.stop()
    return {"stopped": True, **observer.runtime_status()}


@router.get("/meetings")
def list_hub_meetings(limit: int = 100):
    """List locally captured Hub conversations and expose missing task correlation."""
    observer = get_hub_meeting_observer()
    return {
        "meetings": observer.store.list_meetings(limit),
        "observer": observer.runtime_status(),
    }


@router.get("/meetings/{conversation_id}")
def get_hub_meeting(conversation_id: str):
    observer = get_hub_meeting_observer()
    meeting = observer.store.get_meeting(conversation_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Captured DGM-HUB meeting not found.")
    knowledge = _hub_knowledge_store()
    meeting["proposals"] = [
        item for item in knowledge.list_proposals()
        if item.get("source_conversation_id") == conversation_id
    ]
    meeting["decisions"] = [
        item for item in knowledge.list_decisions()
        if item.get("source_conversation_id") == conversation_id
    ]
    return meeting


@router.post("/meetings/{conversation_id}/proposals")
def record_hub_meeting_proposal(
    conversation_id: str,
    payload: HubMeetingProposalRequest,
):
    """Record a human-identified agent proposal linked to one immutable Hub event."""
    observer = get_hub_meeting_observer()
    meeting = observer.store.get_meeting(conversation_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Captured DGM-HUB meeting not found.")
    source = observer.store.get_event(payload.source_event_id)
    if (
        source is None
        or source["conversation_id"] != conversation_id
        or source["kind"] != "provider_response"
    ):
        raise HTTPException(
            status_code=422,
            detail="Proposal source must be a captured provider_response from this meeting.",
        )
    proposal = AIProposal(
        proposal_id=f"hubproposal_{uuid4().hex}",
        statement=payload.statement.strip(),
        source_conversation_id=conversation_id,
        source_message_id=payload.source_event_id,
    )
    try:
        _hub_knowledge_store().save_proposal(proposal)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "proposal_id": proposal.proposal_id,
        "source_conversation_id": conversation_id,
        "source_event_id": payload.source_event_id,
        "accepted": None,
        "status": "unreviewed_proposal",
    }


@router.post("/meetings/{conversation_id}/decision")
def record_hub_meeting_decision(
    conversation_id: str,
    payload: HubMeetingDecisionRequest,
    request: Request,
):
    """Persist an explicit operator-confirmed decision; agent consensus is never enough."""
    if payload.confirm is not True:
        raise HTTPException(
            status_code=400,
            detail="Explicit confirm=true is required to record an operator decision.",
        )
    principal = getattr(request.state, "dgm_principal", {}) or {}
    if not isinstance(principal, dict):
        raise HTTPException(status_code=401, detail="Authenticated operator identity is unavailable.")
    session_id = principal.get("session_id")
    actor = principal.get("subject") or session_id
    if not isinstance(session_id, str) or not session_id or not isinstance(actor, str) or not actor:
        raise HTTPException(status_code=401, detail="Authenticated operator identity is unavailable.")

    observer = get_hub_meeting_observer()
    meeting = observer.store.get_meeting(conversation_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Captured DGM-HUB meeting not found.")
    source_message_id = None
    if payload.source_event_id:
        source = observer.store.get_event(payload.source_event_id)
        if (
            source is None
            or source["conversation_id"] != conversation_id
            or source["kind"] != "user_message"
        ):
            raise HTTPException(
                status_code=422,
                detail="Decision source must be a captured operator message from this meeting.",
            )
        source_message_id = payload.source_event_id

    accepted = list(dict.fromkeys(payload.accepted_proposal_ids))
    rejected = list(dict.fromkeys(payload.rejected_proposal_ids))
    if set(accepted) & set(rejected):
        raise HTTPException(status_code=422, detail="A proposal cannot be both accepted and rejected.")
    knowledge = _hub_knowledge_store()
    proposals = {item["proposal_id"]: item for item in knowledge.list_proposals()}
    for proposal_id in accepted + rejected:
        proposal = proposals.get(proposal_id)
        if proposal is None or proposal.get("source_conversation_id") != conversation_id:
            raise HTTPException(status_code=422, detail=f"Proposal does not belong to this meeting: {proposal_id}")

    evidence = [
        f"operator_session_id:{session_id}",
        f"meeting_conversation_id:{conversation_id}",
        f"outcome:{payload.outcome}",
        f"rationale:{payload.rationale.strip()}",
    ]
    if source_message_id:
        evidence.append(f"source_event_id:{source_message_id}")
    evidence.extend(f"accepted_proposal_id:{item}" for item in accepted)
    evidence.extend(f"rejected_proposal_id:{item}" for item in rejected)

    decision = UserDecision(
        decision_id=f"hubdecision_{uuid4().hex}",
        statement=f"{payload.outcome.upper()}: {payload.statement.strip()}",
        status="confirmed",
        source_conversation_id=conversation_id,
        source_message_id=source_message_id,
        decided_at=datetime.now(timezone.utc).isoformat(),
        evidence=evidence,
        confirmed_by_user=True,
    )
    try:
        knowledge.save_decision_with_proposals(
            decision,
            accepted_proposal_ids=accepted,
            rejected_proposal_ids=rejected,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "decision_id": decision.decision_id,
        "statement": decision.statement,
        "status": decision.status,
        "confirmed_by_user": decision.confirmed_by_user,
        "source_conversation_id": conversation_id,
        "source_message_id": source_message_id,
        "accepted_proposal_ids": accepted,
        "rejected_proposal_ids": rejected,
        "evidence": evidence,
    }
