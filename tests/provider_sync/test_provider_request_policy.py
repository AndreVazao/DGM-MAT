# Path: C:\\ProgramasGodMode\\DGM-MAT\\tests\\provider_sync\\test_provider_request_policy.py

import pytest

from core.governance.provider_rate_control import ProviderRateControl
from core.provider_sync.provider_registry import ProviderRegistry
from core.provider_sync.provider_request_policy import ProviderRequestPolicy
from core.providers.base.provider_base import ProviderBase


class ObservedProvider(ProviderBase):
    def __init__(self, name="provider-a", available=True):
        super().__init__(name)
        self._available = available
        self.health_metrics["last_check"] = 1
        self.health_metrics["status"] = "ok"

    def is_available(self):
        return self._available


class RecordingRateControl:
    def __init__(self, result=True):
        self.result = result
        self.calls = []

    def allow_request(self, provider_id):
        self.calls.append(provider_id)
        return self.result


def make_policy(provider=None, rate_control=None):
    registry = ProviderRegistry()
    if provider is not None:
        registry.register(provider.name, provider)
    rate_control = rate_control or RecordingRateControl()
    return ProviderRequestPolicy(registry, rate_control), rate_control


def evaluate(policy, **overrides):
    request = {
        "provider_id": "provider-a",
        "request_id": "request-001",
        "operation": "chat",
    }
    request.update(overrides)
    return policy.evaluate(**request)


def test_policy_allows_registered_observed_provider_without_executing_it():
    provider = ObservedProvider()
    policy, rate = make_policy(provider)

    decision = evaluate(policy)

    assert decision.allowed is True
    assert decision.code == "allowed"
    assert decision.rate_limit_consumed is True
    assert rate.calls == ["provider-a"]


@pytest.mark.parametrize(
    ("overrides", "expected_code"),
    [
        ({"provider_id": ""}, "invalid_request"),
        ({"request_id": ""}, "invalid_request"),
        ({"operation": "shell"}, "unsupported_operation"),
    ],
)
def test_policy_rejects_invalid_or_unsupported_requests(overrides, expected_code):
    policy, rate = make_policy(ObservedProvider())

    decision = evaluate(policy, **overrides)

    assert decision.allowed is False
    assert decision.code == expected_code
    assert rate.calls == []


def test_policy_rejects_unregistered_provider_before_rate_limit():
    policy, rate = make_policy()

    decision = evaluate(policy)

    assert decision.code == "provider_not_registered"
    assert rate.calls == []


def test_policy_rejects_unavailable_provider_before_rate_limit():
    policy, rate = make_policy(ObservedProvider(available=False))

    decision = evaluate(policy)

    assert decision.code == "provider_unavailable"
    assert rate.calls == []


def test_policy_requires_explicit_approval_before_consuming_rate_limit():
    policy, rate = make_policy(ObservedProvider())

    decision = evaluate(policy, operation="write", approval_required=True, approved=False)

    assert decision.code == "approval_required"
    assert decision.approval_required is True
    assert rate.calls == []


def test_policy_continues_after_explicit_approval():
    policy, rate = make_policy(ObservedProvider())

    decision = evaluate(policy, operation="write", approval_required=True, approved=True)

    assert decision.allowed is True
    assert decision.approval_required is True
    assert rate.calls == ["provider-a"]


def test_policy_fails_closed_when_rate_control_rejects():
    policy, rate = make_policy(ObservedProvider(), RecordingRateControl(result=False))

    decision = evaluate(policy)

    assert decision.code == "rate_limited"
    assert decision.allowed is False


def test_policy_fails_closed_when_health_check_raises():
    provider = ObservedProvider()

    def raise_health():
        raise RuntimeError("synthetic failure")

    provider.is_available = raise_health
    policy, rate = make_policy(provider)

    decision = evaluate(policy)

    assert decision.code == "health_check_error"
    assert rate.calls == []


def test_policy_fails_closed_when_registry_raises():
    policy, rate = make_policy(ObservedProvider())

    def raise_lookup(_provider_id):
        raise RuntimeError("synthetic registry failure")

    policy._registry.get_provider = raise_lookup

    decision = evaluate(policy)

    assert decision.code == "registry_error"
    assert rate.calls == []


def test_policy_fails_closed_when_rate_control_raises():
    policy, _ = make_policy(ObservedProvider())

    def raise_rate(_provider_id):
        raise RuntimeError("synthetic rate failure")

    policy._rate_control.allow_request = raise_rate

    decision = evaluate(policy)

    assert decision.code == "rate_control_error"
    assert decision.allowed is False


@pytest.mark.parametrize("operation", ["tool", "browser", "execute", "write"])
def test_side_effecting_operation_cannot_bypass_approval_flag(operation):
    policy, rate = make_policy(ObservedProvider())

    decision = evaluate(policy, operation=operation)

    assert decision.allowed is False
    assert decision.code == "approval_required"
    assert decision.approval_required is True
    assert rate.calls == []


@pytest.mark.parametrize("flag_value", ["false", 0, 1, None])
def test_policy_rejects_non_boolean_approval_flags(flag_value):
    policy, rate = make_policy(ObservedProvider())

    decision = evaluate(policy, approval_required=flag_value)

    assert decision.allowed is False
    assert decision.code == "invalid_request"
    assert rate.calls == []
