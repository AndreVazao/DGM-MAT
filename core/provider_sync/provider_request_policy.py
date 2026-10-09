# Path: C:\\ProgramasGodMode\\DGM-MAT\\core\\provider_sync\\provider_request_policy.py
"""Fail-closed preflight policy for future governed provider requests.

This module deliberately does not call adapters or retrieve credentials. It only
returns a decision; execution must remain in a separately approved service layer.
"""
from dataclasses import dataclass

from core.governance.provider_rate_control import ProviderRateControl
from core.provider_sync.provider_registry import ProviderRegistry


@dataclass(frozen=True)
class ProviderRequestDecision:
    allowed: bool
    code: str
    reason: str
    provider_id: str
    request_id: str
    approval_required: bool
    rate_limit_consumed: bool = False


class ProviderRequestPolicy:
    """Evaluate registration, observed availability, approval, then rate limit."""

    def __init__(
        self,
        registry: ProviderRegistry,
        rate_control: ProviderRateControl,
    ) -> None:
        self._registry = registry
        self._rate_control = rate_control

    def evaluate(
        self,
        *,
        provider_id: str,
        request_id: str,
        operation: str,
        approval_required: bool = False,
        approved: bool = False,
    ) -> ProviderRequestDecision:
        """Return a decision only; never execute the provider operation.

        Unknown operations and missing identifiers fail closed. Known side-effecting
        operation classes always require approval; the trusted service may require
        approval for additional operations as its risk classification evolves.
        """
        provider_id = provider_id.strip() if isinstance(provider_id, str) else ""
        request_id = request_id.strip() if isinstance(request_id, str) else ""
        operation = operation.strip().lower() if isinstance(operation, str) else ""
        requires_approval = approval_required or operation in {"tool", "browser", "execute", "write"}

        def deny(code: str, reason: str, required: bool = requires_approval):
            return ProviderRequestDecision(
                allowed=False,
                code=code,
                reason=reason,
                provider_id=provider_id,
                request_id=request_id,
                approval_required=required,
            )

        if not provider_id or not request_id:
            return deny("invalid_request", "provider_id and request_id are required")
        if type(approval_required) is not bool or type(approved) is not bool:
            return deny("invalid_request", "approval flags must be booleans")
        if operation not in {"chat", "completion", "tool", "browser", "execute", "write"}:
            return deny("unsupported_operation", "operation is not in the governed operation allowlist")

        # Conservative built-in floor: callers cannot downgrade known side-effecting
        # operation classes by omitting the approval_required flag.
        if requires_approval and not approved:
            return deny("approval_required", "explicit approval is required before execution", True)

        try:
            provider = self._registry.get_provider(provider_id)
        except Exception:
            return deny("registry_error", "provider registry lookup failed")
        if provider is None:
            return deny("provider_not_registered", "provider is not explicitly registered")

        try:
            available = provider.is_available()
        except Exception:
            return deny("health_check_error", "provider availability check raised an exception")
        if available is not True:
            return deny("provider_unavailable", "provider has no currently accepted availability observation")

        # External provider calls are allowed only when the adapter's trusted
        # registration explicitly verifies free-tier billing and a known quota.
        # Unknown pricing/quota is not interpreted as free.
        capabilities = getattr(provider, "capabilities", None)
        config = getattr(provider, "config", None)
        health = getattr(provider, "health_metrics", None)
        if not isinstance(capabilities, dict) or not isinstance(config, dict) or not isinstance(health, dict):
            return deny("cost_or_quota_unknown", "provider cost and quota metadata are unavailable")
        cost_profile = capabilities.get("cost_profile")
        billing_mode = config.get("billing_mode")
        cost_verified = config.get("cost_verified")
        if cost_profile != "free" or billing_mode != "free_tier" or cost_verified is not True:
            return deny("paid_or_unverified_provider_blocked", "only explicitly verified free-tier providers are allowed")
        quota_used = health.get("quota_used")
        quota_limit = health.get("quota_limit")
        if (
            isinstance(quota_used, bool) or not isinstance(quota_used, int) or quota_used < 0
            or isinstance(quota_limit, bool) or not isinstance(quota_limit, int) or quota_limit <= 0
        ):
            return deny("cost_or_quota_unknown", "free-tier quota must have known non-negative usage and a positive limit")
        if quota_used >= quota_limit:
            return deny("free_quota_exhausted", "free-tier quota is exhausted; wait for reset or choose another verified free route")

        try:
            within_limit = self._rate_control.allow_request(provider_id)
        except Exception:
            return deny("rate_control_error", "provider rate-control check failed closed")
        if within_limit is not True:
            return deny("rate_limited", "provider request limit has been reached")

        # Require an adapter-owned local quota reservation so concurrent requests
        # cannot all pass the same stale free-tier usage observation.
        reserve_quota = getattr(provider, "reserve_free_quota", None)
        if not callable(reserve_quota):
            return deny("free_quota_reservation_unavailable", "provider cannot reserve free-tier quota safely")
        try:
            reserved = reserve_quota()
        except Exception:
            return deny("free_quota_reservation_failed", "free-tier quota reservation failed closed")
        if reserved is not True:
            return deny("free_quota_exhausted", "free-tier quota could not be reserved; wait for reset")

        return ProviderRequestDecision(
            allowed=True,
            code="allowed",
            reason="preflight checks passed; no provider operation was executed",
            provider_id=provider_id,
            request_id=request_id,
            approval_required=requires_approval,
            rate_limit_consumed=True,
        )
