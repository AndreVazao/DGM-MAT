# Path: C:\ProgramasGodMode\DGM-MAT\core\api\provider_execution_api.py
"""Authenticated, approval-gated HTTP boundary for governed provider chat."""
from __future__ import annotations

import hmac
import os
import uuid
from typing import Literal, List, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field, constr

from core.governance.provider_rate_control import ProviderRateControl
from core.provider_sync.durable_provider_approval_store import DurableProviderApprovalStore
from core.provider_sync.governed_provider_service import GovernedProviderService
from core.provider_sync.provider_request_policy import ProviderRequestPolicy
from core.provider_sync.provider_registry import provider_registry

router = APIRouter(prefix="/provider-execution", tags=["provider-execution"])
_rate_control = ProviderRateControl(max_requests=10)


class ProviderMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: constr(strip_whitespace=True, min_length=1, max_length=12000)

    model_config = ConfigDict(extra="forbid")


class ProviderRequest(BaseModel):
    provider_id: constr(strip_whitespace=True, min_length=1, max_length=128)
    request_id: constr(strip_whitespace=True, min_length=1, max_length=256)
    messages: List[ProviderMessage] = Field(min_length=1, max_length=40)

    model_config = ConfigDict(extra="forbid")


class ApprovalDecision(BaseModel):
    decision: Literal["approve", "reject"]
    reason: constr(max_length=1000) = ""

    model_config = ConfigDict(extra="forbid")


class ProviderExecutionRequest(BaseModel):
    approval_task_id: constr(strip_whitespace=True, min_length=1, max_length=256)

    model_config = ConfigDict(extra="forbid")


def _configured_tokens() -> tuple[str, str]:
    api_token = os.getenv("DGM_PROVIDER_API_TOKEN", "").strip()
    operator_token = os.getenv("DGM_PROVIDER_OPERATOR_TOKEN", "").strip()
    if not api_token or not operator_token or hmac.compare_digest(api_token, operator_token):
        raise HTTPException(
            status_code=503,
            detail="Provider API is disabled: distinct API and operator credentials must be configured.",
        )
    return api_token, operator_token


def _authorize(authorization: Optional[str], *, operator: bool) -> None:
    api_token, operator_token = _configured_tokens()
    expected = operator_token if operator else api_token
    if not isinstance(authorization, str):
        raise HTTPException(status_code=401, detail="Bearer authentication required.")
    scheme, separator, supplied = authorization.partition(" ")
    if not separator or scheme.lower() != "bearer" or not supplied.strip():
        raise HTTPException(status_code=401, detail="Bearer authentication required.")
    if not hmac.compare_digest(supplied.strip(), expected):
        raise HTTPException(status_code=401, detail="Invalid credentials.")


def _get_approval_store() -> DurableProviderApprovalStore:
    return DurableProviderApprovalStore()


def _get_provider_service() -> GovernedProviderService:
    policy = ProviderRequestPolicy(provider_registry, _rate_control)
    return GovernedProviderService(policy, _get_approval_store())


def _safe_approval_payload(item: dict) -> dict:
    payload = item.get("payload", {})
    if not isinstance(payload, dict) or not payload.get("provider_request_fingerprint"):
        raise HTTPException(status_code=409, detail="Approval record is not a governed provider request.")
    return {
        "approval_task_id": payload.get("task_id"),
        "status": str(item.get("status", "")),
        "provider_id": payload.get("provider_id"),
        "request_id": payload.get("request_id"),
        "messages": payload.get("messages", []),
        "created_at": item.get("created_at"),
        "approved_by": item.get("approved_by"),
        "approved_at": item.get("approved_at"),
    }


@router.post("/requests", status_code=201)
def request_provider_execution(
    request: ProviderRequest,
    authorization: Optional[str] = Header(default=None),
):
    """Create a durable approval request; this endpoint never calls a provider."""
    _authorize(authorization, operator=False)
    messages = [{"role": item.role, "content": item.content} for item in request.messages]
    if not GovernedProviderService._valid_messages(messages):
        raise HTTPException(status_code=422, detail="Provider message envelope is invalid or exceeds limits.")
    fingerprint = GovernedProviderService.request_fingerprint(
        request.provider_id, request.request_id, messages
    )
    task_id = "provider-" + uuid.uuid4().hex
    total_chars = sum(len(item["content"]) for item in messages)
    summary = (
        f"Provider chat request; provider={request.provider_id}; request_id={request.request_id}; "
        f"messages={len(messages)}; input_chars={total_chars}"
    )
    try:
        _get_approval_store().request_provider_approval(
            task_id=task_id,
            provider_request_fingerprint=fingerprint,
            summary=summary,
            provider_id=request.provider_id,
            request_id=request.request_id,
            messages=messages,
            risk_score=0.0,
            impact="MEDIUM",
        )
    except Exception:
        raise HTTPException(status_code=503, detail="Durable approval storage is unavailable.")
    return {
        "status": "awaiting_approval",
        "approval_task_id": task_id,
        "provider_id": request.provider_id,
        "request_id": request.request_id,
        "message_count": len(messages),
        "input_chars": total_chars,
        "approval_required": True,
    }


@router.get("/approvals")
def list_provider_approvals(authorization: Optional[str] = Header(default=None)):
    """Operator-only queue view; includes exact message content for informed review."""
    _authorize(authorization, operator=True)
    try:
        queue = _get_approval_store()._queue
        pending = queue.list_pending_approvals()
    except Exception:
        raise HTTPException(status_code=503, detail="Durable approval storage is unavailable.")
    results = []
    for item in pending:
        payload = item.get("payload", {})
        if isinstance(payload, dict) and payload.get("provider_request_fingerprint"):
            results.append(_safe_approval_payload(item))
    return {"status": "success", "approvals": results}


@router.post("/approvals/{approval_task_id}/decision")
def decide_provider_approval(
    approval_task_id: str,
    decision: ApprovalDecision,
    authorization: Optional[str] = Header(default=None),
):
    """Operator-only durable approve/reject; no provider execution occurs here."""
    _authorize(authorization, operator=True)
    if not approval_task_id.startswith("provider-"):
        raise HTTPException(status_code=404, detail="Provider approval request not found.")
    try:
        store = _get_approval_store()
        current = store.get_approval(approval_task_id)
        payload = current.get("payload", {}) if isinstance(current, dict) else {}
        if not isinstance(payload, dict) or not payload.get("provider_request_fingerprint"):
            raise HTTPException(status_code=404, detail="Provider approval request not found.")
        if current.get("status") != "QUEUED":
            raise HTTPException(status_code=409, detail="Approval request already has a decision or was consumed.")
        operator_id = os.getenv("DGM_PROVIDER_OPERATOR_ID", "authenticated-operator").strip()
        if not operator_id or len(operator_id) > 255:
            raise HTTPException(status_code=503, detail="Operator identity configuration is invalid.")
        if decision.decision == "approve":
            changed = store._queue.approve_approval(approval_task_id, operator=operator_id)
        else:
            changed = store._queue.reject_approval(
                approval_task_id, reason=decision.reason, operator=operator_id
            )
        if not changed:
            raise HTTPException(status_code=409, detail="Approval state changed; refresh the queue.")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=503, detail="Durable approval storage is unavailable.")
    return {
        "status": "approved" if decision.decision == "approve" else "rejected",
        "approval_task_id": approval_task_id,
        "operator": operator_id,
    }


@router.post("/execute")
async def execute_approved_provider_request(
    request: ProviderExecutionRequest,
    authorization: Optional[str] = Header(default=None),
):
    """Execute only the exact message envelope reviewed and durably approved by an operator."""
    _authorize(authorization, operator=False)
    task_id = request.approval_task_id
    if not task_id.startswith("provider-"):
        raise HTTPException(status_code=404, detail="Provider approval request not found.")
    try:
        store = _get_approval_store()
        approval = store.get_approval(task_id)
    except Exception:
        raise HTTPException(status_code=503, detail="Durable approval storage is unavailable.")
    if not isinstance(approval, dict):
        raise HTTPException(status_code=404, detail="Provider approval request not found.")
    payload = approval.get("payload", {})
    if not isinstance(payload, dict) or not payload.get("provider_request_fingerprint"):
        raise HTTPException(status_code=404, detail="Provider approval request not found.")
    if approval.get("status") != "APPROVED":
        raise HTTPException(status_code=409, detail="Provider request has not been approved or was already consumed.")
    provider_id = payload.get("provider_id")
    request_id = payload.get("request_id")
    messages = payload.get("messages")
    if not isinstance(provider_id, str) or not isinstance(request_id, str) or not isinstance(messages, list):
        raise HTTPException(status_code=409, detail="Stored provider request is incomplete.")
    try:
        result = await _get_provider_service().execute_chat(
            provider_id=provider_id,
            request_id=request_id,
            messages=messages,
            approval_task_id=task_id,
        )
    except Exception:
        raise HTTPException(status_code=503, detail="Governed provider service failed closed.")
    try:
        store.record_execution_outcome(
            task_id,
            success=result.success,
            code=result.code,
            elapsed_ms=result.elapsed_ms,
        )
    except Exception:
        # Do not expose adapter details; the approval remains consumed if already claimed.
        pass
    if not result.success:
        status_code = 504 if result.code == "provider_timeout" else (
            503 if result.code in {"provider_unavailable", "provider_not_registered", "registry_error"} else 409
        )
        raise HTTPException(status_code=status_code, detail={"code": result.code})
    return {
        "status": "completed",
        "request_id": result.request_id,
        "provider_id": result.provider_id,
        "response": result.response,
        "elapsed_ms": result.elapsed_ms,
    }
