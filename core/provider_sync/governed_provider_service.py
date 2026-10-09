# Path: C:\\ProgramasGodMode\\DGM-MAT\\core\\provider_sync\\governed_provider_service.py
"""Bounded fail-closed chat execution for explicitly registered providers."""
import asyncio
import hashlib
import json
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from core.provider_sync.provider_request_policy import ProviderRequestPolicy
from core.provider_sync.durable_provider_approval_store import DurableProviderApprovalStore


@dataclass(frozen=True)
class ProviderExecutionResult:
    success: bool
    code: str
    request_id: str
    provider_id: str
    response: Optional[str] = None
    elapsed_ms: Optional[float] = None


class GovernedProviderService:
    """Execute one bounded chat call; other operation types are not supported."""
    MAX_MESSAGES = 40
    MAX_MESSAGE_CHARS = 12000
    MAX_TOTAL_INPUT_CHARS = 30000
    MAX_RESPONSE_CHARS = 50000
    DEFAULT_TIMEOUT_SECONDS = 30.0
    MAX_TIMEOUT_SECONDS = 60.0
    def __init__(self, policy: ProviderRequestPolicy, approval_store: Optional[Any] = None, *, timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS):
        if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)):
            raise ValueError("timeout_seconds must be numeric")
        if timeout_seconds <= 0 or timeout_seconds > self.MAX_TIMEOUT_SECONDS:
            raise ValueError("timeout_seconds is outside the permitted range")
        self._policy = policy
        self._approval_store = approval_store if approval_store is not None else DurableProviderApprovalStore()
        self._timeout_seconds = float(timeout_seconds)

    @staticmethod
    def request_fingerprint(provider_id: str, request_id: str, messages: List[Dict[str, str]]) -> str:
        envelope = {"provider_id": provider_id, "request_id": request_id, "messages": messages}
        canonical = json.dumps(envelope, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _approved_durably(self, task_id: str, fingerprint: str) -> bool:
        if not isinstance(task_id, str) or not task_id.strip():
            return False
        try:
            approval = self._approval_store.get_approval(task_id.strip())
        except Exception:
            return False
        return (
            isinstance(approval, dict)
            and approval.get("status") == "APPROVED"
            and bool(approval.get("approved_by"))
            and bool(approval.get("approved_at"))
            and approval.get("provider_request_fingerprint") == fingerprint
        )

    @staticmethod
    def _redact_response(response: str) -> str:
        patterns = (
            (r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{12,}", "Bearer [REDACTED]"),
            (r"(?i)\b(?:api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret|password)\s*[:=]\s*[\"']?[^\s\"',;]{8,}", "credential=[REDACTED]"),
            (r"\bsk-[A-Za-z0-9_-]{20,}", "[REDACTED_KEY]"),
            (r"\bnvapi-[A-Za-z0-9_-]{20,}", "[REDACTED_KEY]"),
            (r"\bgh[pousr]_[A-Za-z0-9_]{20,}", "[REDACTED_KEY]"),
            (r"\bAKIA[0-9A-Z]{16}\b", "[REDACTED_KEY]"),
        )
        redacted = response
        for pattern, replacement in patterns:
            redacted = re.sub(pattern, replacement, redacted)
        return redacted

    @classmethod
    def _valid_messages(cls, messages: Any) -> bool:
        if not isinstance(messages, list) or not messages or len(messages) > cls.MAX_MESSAGES:
            return False
        total = 0
        for message in messages:
            if not isinstance(message, dict) or set(message) != {"role", "content"}:
                return False
            role, content = message.get("role"), message.get("content")
            if role not in {"system", "user", "assistant"} or not isinstance(content, str) or not content.strip():
                return False
            if len(content) > cls.MAX_MESSAGE_CHARS:
                return False
            total += len(content)
            if total > cls.MAX_TOTAL_INPUT_CHARS:
                return False
        return True

    async def execute_chat(self, *, provider_id: str, request_id: str, messages: List[Dict[str, str]], approval_task_id: Optional[str] = None) -> ProviderExecutionResult:
        """Call the adapter at most once after all checks pass; never retry."""
        provider_id = provider_id.strip() if isinstance(provider_id, str) else ""
        request_id = request_id.strip() if isinstance(request_id, str) else ""

        def denied(code: str) -> ProviderExecutionResult:
            return ProviderExecutionResult(False, code, request_id, provider_id)

        if not provider_id or not request_id or len(provider_id) > 128 or len(request_id) > 256:
            return denied("invalid_request")
        if not self._valid_messages(messages):
            return denied("invalid_messages")

        requires_approval = approval_task_id is not None
        fingerprint = self.request_fingerprint(provider_id, request_id, messages)
        approved = self._approved_durably(approval_task_id, fingerprint) if requires_approval else False
        if requires_approval and not approved:
            return denied("approval_not_durably_approved")
        decision = self._policy.evaluate(
            provider_id=provider_id,
            request_id=request_id,
            operation="chat",
            approval_required=requires_approval,
            approved=approved,
        )
        if not decision.allowed:
            return denied(decision.code)
        try:
            provider = self._policy._registry.get_provider(provider_id)
        except Exception:
            return denied("registry_error")
        if provider is None:
            return denied("provider_not_registered")

        if requires_approval:
            try:
                claim = getattr(self._approval_store, "claim_approval", None)
                if not callable(claim) or claim(approval_task_id, fingerprint) is not True:
                    return denied("approval_already_used_or_unclaimable")
            except Exception:
                return denied("approval_claim_failed")

        started = time.monotonic()
        try:
            response = await asyncio.wait_for(
                provider.chat([{"role": message["role"], "content": message["content"]} for message in messages]),
                timeout=self._timeout_seconds,
            )
        except asyncio.TimeoutError:
            return denied("provider_timeout")
        except Exception:
            return denied("provider_execution_error")

        elapsed_ms = (time.monotonic() - started) * 1000.0
        if not isinstance(response, str):
            return denied("invalid_provider_response")
        if len(response) > self.MAX_RESPONSE_CHARS:
            return denied("provider_response_too_large")
        return ProviderExecutionResult(
            success=True,
            code="completed",
            request_id=request_id,
            provider_id=provider_id,
            response=self._redact_response(response),
            elapsed_ms=round(elapsed_ms, 3),
        )
