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
