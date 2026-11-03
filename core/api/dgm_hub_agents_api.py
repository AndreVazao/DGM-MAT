"""Operator-gated integration with the existing DGM-HUB MultiChat room."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from core.organization.dgm_hub_multichat_bridge import (
    DGMHubMultiChatBridge,
    HubBridgeError,
    HubProviderUnavailable,
    PROVIDER_ROLES,
)

router = APIRouter(prefix="/governance/agents/hub", tags=["external-agents"])


class HubAgentConsultRequest(BaseModel):
    goal: str = Field(min_length=1, max_length=4000)
    context: str = Field(default="", max_length=9000)
    providers: list[str] = Field(min_length=1, max_length=4)
    free_capacity_confirmed: bool = False

    model_config = ConfigDict(extra="forbid")


def _mission_engine():
    # Import lazily to reuse the canonical runtime singleton and avoid API import cycles.
    from core.autonomy.mission_engine import mission_engine
    return mission_engine


def _bridge() -> DGMHubMultiChatBridge:
    return DGMHubMultiChatBridge()


@router.get("/status")
def hub_agent_status():
    """Read-only local Hub status. Does not start providers or send model requests."""
    try:
        return _bridge().get_status()
    except HubBridgeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/consult")
def consult_hub_agents(payload: HubAgentConsultRequest):
    """Request a bounded free-only consultation; persist every answer as untrusted."""
    if payload.free_capacity_confirmed is not True:
        raise HTTPException(
            status_code=400,
            detail="Explicit operator confirmation of current free capacity is required.",
        )
    if len(set(payload.providers)) != len(payload.providers) or any(
        provider not in PROVIDER_ROLES for provider in payload.providers
    ):
        raise HTTPException(status_code=422, detail="Unsupported or duplicate Hub provider.")

    bridge = _bridge()
    engine = _mission_engine()
    packets: dict[str, str] = {}
    try:
        for provider in payload.providers:
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
        raise HTTPException(status_code=422, detail="Consultation packet failed local safety validation.") from exc

    try:
        task = bridge.consult(
            goal=payload.goal,
            context=payload.context,
            providers=payload.providers,
        )
    except HubProviderUnavailable as exc:
        for collaboration_id in packets.values():
            engine.pause_specialist_collaboration(
                collaboration_id,
                reason=f"Provider unavailable in DGM-HUB; no request sent. {str(exc)[:1200]}",
            )
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except HubBridgeError as exc:
        for collaboration_id in packets.values():
            engine.pause_specialist_collaboration(
                collaboration_id,
                reason=f"Hub consultation did not complete; no retry or paid fallback. {str(exc)[:1200]}",
            )
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

    return {
        "status": "completed",
        "hub_task_id": task.task_id,
        "conversation_id": task.conversation_id,
        "room_leader": "operator",
        "dgm_mat_mode": "observer_and_consultation_coordinator",
        "providers": responses,
        "paid_fallback": False,
        "free_capacity_attested_by_operator": True,
        "quota_limitation": "The Hub does not expose numeric remaining quota; rate/capacity errors stop the consultation without retry.",
        "all_results_untrusted": True,
    }
