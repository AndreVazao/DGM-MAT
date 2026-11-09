"""Local queue API for explicit free-tier browser UI consultations."""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field

from core.operations.operation_audit import AuditWriteError, append_command_audit
from core.recovery.browser_consult_store import BrowserConsultStore, PROVIDERS, _enabled

router = APIRouter(prefix="/recovery/browser-consult", tags=["free-tier-browser-consult"])
_store_instance: BrowserConsultStore | None = None


def _store() -> BrowserConsultStore:
    global _store_instance
    if _store_instance is None:
        _store_instance = BrowserConsultStore()
    return _store_instance


def _principal(request: Request) -> dict:
    principal = request.scope.get("state", {}).get("dgm_principal")
    if not isinstance(principal, dict) or not isinstance(principal.get("session_id"), str):
        raise HTTPException(status_code=401, detail="Authenticated local DGM-MAT session required.")
    return principal


def _session_id(request: Request) -> str | None:
    principal = getattr(request.state, "dgm_principal", {}) or {}
    return principal.get("session_id") if isinstance(principal, dict) else None


def _audit(event: str, status: str, request: Request, provider: str = "none") -> None:
    append_command_audit(
        event=event,
        command_id="dgm_browser_consult.free_only:" + provider,
        status=status,
        session_id=_session_id(request),
    )


class BrowserConsultEnqueueRequest(BaseModel):
    task_ref: str = Field(min_length=1, max_length=160)
    goal: str = Field(min_length=1, max_length=4000)
    context: str = Field(default="", max_length=4000)
    providers: list[Literal["chatgpt", "gemini", "grok", "deepseek", "qwen"]] = Field(min_length=1, max_length=5)
    free_capacity_confirmed: bool = False
    review_mode: Literal["standard", "fresh_review"] = "standard"
    review_id: str | None = Field(default=None, min_length=1, max_length=120)

    model_config = ConfigDict(extra="forbid")


class BrowserConsultResultRequest(BaseModel):
    consultation_id: str = Field(min_length=1, max_length=80)
    claim_token: str = Field(min_length=32, max_length=128)
    response_text: str = Field(min_length=1, max_length=16000)
    evidence: dict | None = None

    model_config = ConfigDict(extra="forbid")


class BrowserConsultBlockRequest(BaseModel):
    consultation_id: str = Field(min_length=1, max_length=80)
    claim_token: str = Field(min_length=32, max_length=128)
    reason: Literal["rate_limited", "blocked_login", "blocked_challenge", "ui_mismatch", "interrupted", "secret_content"]

    model_config = ConfigDict(extra="forbid")


@router.get("/status")
def browser_consult_status(request: Request):
    _principal(request)
    return _store().status()


@router.post("/enqueue")
def enqueue_browser_consultation(payload: BrowserConsultEnqueueRequest, request: Request):
    principal = _principal(request)
    if not _enabled():
        raise HTTPException(status_code=409, detail="Free-tier browser consultation is disabled until explicitly enabled on this PC.")
    if payload.free_capacity_confirmed is not True:
        raise HTTPException(status_code=400, detail="Operator must explicitly attest that the selected provider accounts are free-tier.")
    try:
        _audit("command.requested", "queued", request, ",".join(payload.providers))
        result = _store().enqueue(
            task_ref=payload.task_ref,
            goal=payload.goal,
            context=payload.context,
            providers=list(payload.providers),
            review_mode=payload.review_mode,
            review_id=payload.review_id,
        )
    except (AuditWriteError, ValueError, OSError) as exc:
        raise HTTPException(status_code=503, detail="Consultation could not be safely queued or audited.") from exc
    result["approval_required"] = bool(result.get("consultation_ids"))
    result["created_by"] = principal.get("subject", "local-operator")
    return result


@router.post("/approve/{consultation_id}")
def approve_browser_consultation(consultation_id: str, request: Request):
    principal = _principal(request)
    try:
        _audit("command.approved", "approval_requested", request)
    except (AuditWriteError, OSError) as exc:
        raise HTTPException(status_code=503, detail="Approval audit unavailable; consultation remains pending.") from exc
    if not _store().approve(consultation_id, operator=str(principal.get("subject") or "local-operator")):
        raise HTTPException(status_code=409, detail="Consultation is missing or no longer awaiting approval.")
    return {"status": "PENDING", "consultation_id": consultation_id}


@router.post("/next")
def claim_browser_consultation(provider: Literal["chatgpt", "gemini", "grok", "deepseek", "qwen"], request: Request):
    _principal(request)
    try:
        item = _store().claim_next(provider)
        if item is None:
            return {"status": "queue_empty", "next": None}
        try:
            _audit("command.sent", "prompt_released_to_extension", request, provider)
        except (AuditWriteError, OSError):
            _store().block(item["consultation_id"], claim_token=item["claim_token"], reason="interrupted")
            raise
        return {
            "status": "claimed",
            "next": {
                "consultation_id": item["consultation_id"],
                "task_ref": item["task_ref"],
                "provider": item["provider"],
                "prompt": item["prompt"],
                "prompt_sha256": item["prompt_sha256"],
                "claim_token": item["claim_token"],
                "review_mode": item.get("review_mode", "standard"),
                "review_id": item.get("review_id"),
            },
        }
    except (AuditWriteError, OSError) as exc:
        raise HTTPException(status_code=503, detail="Consultation audit unavailable; prompt was not released.") from exc


@router.post("/result")
def complete_browser_consultation(payload: BrowserConsultResultRequest, request: Request):
    _principal(request)
    try:
        result = _store().finish(payload.consultation_id, claim_token=payload.claim_token, response_text=payload.response_text, evidence=payload.evidence)
        task_ref = str(result.get("task_ref") or "")
        if result.get("status") == "COMPLETED" and task_ref.startswith("mobile-thread:"):
            thread_id = task_ref[len("mobile-thread:"):]
            try:
                from core.api.mobile_bridge import service as mobile_service
                mobile_service.store.append_message(
                    thread_id,
                    "assistant",
                    "### " + str(result.get("provider", "AI")).upper() + " (resposta externa não verificada)\n\n" + payload.response_text[:12000],
                    metadata={
                        "browser_consultation_id": payload.consultation_id,
                        "provider": result.get("provider"),
                        "result_trusted": False,
                        "approval_required": True,
                        "paid_fallback": False,
                        "source": "dgm-browser-consultation",
                    },
                )
                result["conversation_updated"] = True
            except Exception:
                result["conversation_warning"] = "local_conversation_update_failed"
        try:
            _audit("command.completed", result["status"], request, result["provider"])
            result["audit_warning"] = None
        except AuditWriteError:
            result["audit_warning"] = "completion_audit_unavailable"
        return result
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Consultation not found.") from exc
    except (ValueError, AuditWriteError, OSError) as exc:
        raise HTTPException(status_code=409, detail="Consultation result could not be safely committed.") from exc


@router.post("/block")
def block_browser_consultation(payload: BrowserConsultBlockRequest, request: Request):
    _principal(request)
    try:
        result = _store().block(payload.consultation_id, claim_token=payload.claim_token, reason=payload.reason)
        try:
            _audit("command.blocked", result["status"], request, result["provider"])
            result["audit_warning"] = None
        except AuditWriteError:
            result["audit_warning"] = "block_audit_unavailable"
        return result
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Consultation not found.") from exc
    except (ValueError, AuditWriteError, OSError) as exc:
        raise HTTPException(status_code=409, detail="Consultation blocker could not be safely recorded.") from exc
