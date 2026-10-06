"""Adapters between DGM-MAT runtime models and DGM-Contracts."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Mapping
from dgm_contracts import ApprovalDecision, ApprovalRequest, EventEnvelope, ExecutionRequest, MissionState

def _utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def action_payload_to_execution_request(payload: Mapping[str, Any], *, actor: str = "system", source: str = "dgm-mat.safe_action_queue", tool_name: str = "mission_execution", operation: str = "execute", risk_class: str = "LOW", approval_required: bool = True, timeout_seconds: float | None = None) -> ExecutionRequest:
    mission_id = payload.get("mission_id")
    return ExecutionRequest(actor=actor, source=source, tool_name=tool_name, operation=operation, arguments=dict(payload), target=mission_id, resource=mission_id, risk_class=risk_class, approval_required=approval_required, timeout_seconds=timeout_seconds, mission_id=mission_id, idempotency_key=f"mission:{mission_id}" if mission_id else None)


def approval_to_contract(task_id: str, data: Mapping[str, Any], *, requested_by: str = "dgm-mat", request_id: str | None = None, mission_id: str | None = None) -> ApprovalRequest:
    status = getattr(data.get("status"), "value", data.get("status"))
    status_map = {"awaiting_approval": "PENDING", "approved": "APPROVED", "rejected": "REJECTED"}
    created_at = data.get("requested_at")
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    return ApprovalRequest(approval_id=f"approval:{task_id}", request_id=request_id, mission_id=mission_id, requested_by=requested_by, summary=f"Approval required for task {task_id}", diff_preview=data.get("diff"), risk_class=str(data.get("risk_score", 0.0)), impact=str(data.get("impact", "LOW")), created_at=_utc(created_at) or datetime.now(timezone.utc), status=status_map.get(status, "PENDING"))


def decision_to_contract(approval_id: str, decision: str, *, decided_by: str = "manual", reason: str | None = None, correlation_id: str | None = None) -> ApprovalDecision:
    normalized = decision.upper()
    if normalized not in {"APPROVED", "REJECTED", "CANCELLED"}:
        raise ValueError(f"Unsupported approval decision: {decision}")
    return ApprovalDecision(approval_id=approval_id, decision=normalized, decided_by=decided_by, reason=reason, correlation_id=correlation_id)


def event_to_contract(event: Any) -> EventEnvelope:
    priority = getattr(event.priority, "value", str(event.priority))
    return EventEnvelope(event_id=event.id, timestamp=_utc(event.timestamp) or datetime.now(timezone.utc), source=event.source, target=event.target, event_type=event.event_type, payload=dict(event.payload), priority=priority, scope=event.scope, domain=event.domain, ttl=event.ttl, ecosystem=event.ecosystem, trace_id=event.trace_id, parent_trace_id=event.parent_trace_id, depth=event.depth)


def mission_to_contract(mission: Any) -> MissionState:
    status = getattr(mission.status, "value", str(mission.status))
    return MissionState(mission_id=mission.mission_id, goal=mission.goal, description=mission.description, status=status, progress=mission.progress, error=mission.error, metadata=dict(mission.metadata), created_at=_utc(mission.created_at) or datetime.now(timezone.utc), updated_at=_utc(mission.updated_at) or datetime.now(timezone.utc))
