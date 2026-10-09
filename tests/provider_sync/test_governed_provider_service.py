# Path: C:\\ProgramasGodMode\\DGM-MAT\\tests\\provider_sync\\test_governed_provider_service.py
import asyncio
import pytest

from core.governance.provider_rate_control import ProviderRateControl
from core.provider_sync.provider_registry import ProviderRegistry
from core.provider_sync.provider_request_policy import ProviderRequestPolicy
from core.provider_sync.governed_provider_service import GovernedProviderService
from core.providers.base.provider_base import ProviderBase


class FakeProvider(ProviderBase):
    def __init__(self, name="provider-a", response="hello", delay=0):
        super().__init__(name)
        self.health_metrics["last_check"] = 1
        self.health_metrics["status"] = "ok"
        self.health_metrics["quota_used"] = 0
        self.health_metrics["quota_limit"] = 10
        self.capabilities["cost_profile"] = "free"
        self.config.update({"billing_mode": "free_tier", "cost_verified": True})
        self.calls = 0
        self.response = response
        self.delay = delay

    def reserve_free_quota(self):
        used = self.health_metrics["quota_used"]
        limit = self.health_metrics["quota_limit"]
        if used >= limit:
            return False
        self.health_metrics["quota_used"] = used + 1
        return True

    async def chat(self, messages, **kwargs):
        self.calls += 1
        if self.delay:
            await asyncio.sleep(self.delay)
        return self.response


class FakeRate:
    def __init__(self):
        self.calls = []

    def allow_request(self, provider_id):
        self.calls.append(provider_id)
        return True
class FakeApprovalStore:
    def __init__(self, records=None, raises=False):
        self.records = records or {}
        self.raises = raises

    def get_approval(self, task_id):
        if self.raises:
            raise RuntimeError("synthetic database failure")
        return self.records.get(task_id)

    def claim_approval(self, task_id, expected_fingerprint):
        if self.raises:
            raise RuntimeError("synthetic claim failure")
        record = self.records.get(task_id)
        if not isinstance(record, dict) or record.get("status") != "APPROVED":
            return False
        if record.get("provider_request_fingerprint") != expected_fingerprint:
            return False
        self.records[task_id] = {**record, "status": "RUNNING"}
        return True


def setup(provider=None, approvals=None, timeout=0.05):
    registry = ProviderRegistry()
    if provider is not None:
        registry.register(provider.name, provider)
    rate = FakeRate()
    policy = ProviderRequestPolicy(registry, rate)
    store = FakeApprovalStore(approvals)
    service = GovernedProviderService(policy, store, timeout_seconds=timeout)
    return service, rate, store


def call(service, **overrides):
    args = {
        "provider_id": "provider-a",
        "request_id": "req-001",
        "messages": [{"role": "user", "content": "hello"}],
    }
    args.update(overrides)
    return asyncio.run(service.execute_chat(**args))


def approved_record():
    fingerprint = GovernedProviderService.request_fingerprint(
        "provider-a", "req-001", [{"role": "user", "content": "hello"}]
    )
    return {
        "status": "APPROVED",
        "approved_by": "operator",
        "approved_at": "2026-10-09T10:00:00",
        "provider_request_fingerprint": fingerprint,
    }
def test_service_executes_registered_provider_exactly_once():
    provider = FakeProvider()
    service, rate, _ = setup(provider)
    result = call(service)
    assert result.success is True
    assert result.code == "completed"
    assert result.response == "hello"
    assert provider.calls == 1
    assert rate.calls == ["provider-a"]


def test_service_rejects_unregistered_provider_without_adapter_call():
    provider = FakeProvider()
    service, rate, _ = setup()
    result = call(service)
    assert result.code == "provider_not_registered"
    assert provider.calls == 0
    assert rate.calls == []


@pytest.mark.parametrize("messages", [[], "hello", [{}], [{"role": "system", "content": ""}], [{"role": "developer", "content": "x"}], [{"role": "user", "content": "x", "tool_calls": [{"name": "run"}]}]])
def test_service_rejects_malformed_messages_without_call(messages):
    provider = FakeProvider()
    service, rate, _ = setup(provider)
    result = call(service, messages=messages)
    assert result.code == "invalid_messages"
    assert provider.calls == 0
    assert rate.calls == []


def test_service_rejects_oversized_message_without_call():
    provider = FakeProvider()
    service, rate, _ = setup(provider)
    result = call(service, messages=[{"role": "user", "content": "x" * (service.MAX_MESSAGE_CHARS + 1)}])
    assert result.code == "invalid_messages"
    assert provider.calls == 0
    assert rate.calls == []
def test_service_requires_durable_approval_when_task_id_supplied():
    provider = FakeProvider()
    service, rate, _ = setup(provider)
    result = call(service, approval_task_id="task-1")
    assert result.code == "approval_not_durably_approved"
    assert provider.calls == 0
    assert rate.calls == []


def test_service_accepts_durable_approval_for_explicitly_gated_chat():
    provider = FakeProvider()
    service, rate, _ = setup(provider, {"task-1": approved_record()})
    result = call(service, approval_task_id="task-1")
    assert result.success is True
    assert provider.calls == 1
    assert rate.calls == ["provider-a"]


def test_approval_cannot_be_reused_for_a_second_execution():
    provider = FakeProvider()
    service, rate, _ = setup(provider, {"task-1": approved_record()})
    first = call(service, approval_task_id="task-1")
    second = call(service, request_id="req-002", approval_task_id="task-1")
    assert first.success is True
    assert second.code == "approval_not_durably_approved"
    assert provider.calls == 1
    assert rate.calls == ["provider-a"]


def test_service_fails_closed_if_approval_store_raises():
    provider = FakeProvider()
    registry = ProviderRegistry()
    registry.register(provider.name, provider)
    rate = FakeRate()
    service = GovernedProviderService(ProviderRequestPolicy(registry, rate), FakeApprovalStore(raises=True))
    result = call(service, approval_task_id="task-1")
    assert result.code == "approval_not_durably_approved"
    assert provider.calls == 0
    assert rate.calls == []
def test_service_times_out_without_retrying_provider():
    provider = FakeProvider(delay=0.2)
    service, rate, _ = setup(provider, timeout=0.01)
    result = call(service)
    assert result.code == "provider_timeout"
    assert provider.calls == 1
    assert rate.calls == ["provider-a"]


def test_service_does_not_return_oversized_response():
    provider = FakeProvider(response="x" * (GovernedProviderService.MAX_RESPONSE_CHARS + 1))
    service, _, _ = setup(provider)
    result = call(service)
    assert result.code == "provider_response_too_large"
    assert result.response is None
    assert provider.calls == 1


def test_service_sanitizes_provider_exceptions():
    class ExplodingProvider(FakeProvider):
        async def chat(self, messages, **kwargs):
            self.calls += 1
            raise RuntimeError("secret token must not leak")
    provider = ExplodingProvider()
    service, _, _ = setup(provider)
    result = call(service)
    assert result.code == "provider_execution_error"
    assert "secret token" not in str(result)


def test_service_redacts_common_secret_patterns_from_provider_response():
    provider = FakeProvider(response="Authorization: Bearer abcdefghijklmnopqrstuvwxyz api_key=supersecretvalue123")
    service, _, _ = setup(provider)
    result = call(service)
    assert result.success is True
    assert "abcdefghijklmnopqrstuvwxyz" not in result.response
    assert "supersecretvalue123" not in result.response
    assert "[REDACTED]" in result.response


def test_service_rejects_non_string_provider_response():
    provider = FakeProvider(response={"unexpected": "object"})
    service, _, _ = setup(provider)
    result = call(service)
    assert result.code == "invalid_provider_response"
    assert result.response is None


def test_service_rejects_approval_record_without_operator_or_timestamp():
    provider = FakeProvider()
    service, rate, _ = setup(provider, {"task-1": {"status": "APPROVED", "approved_by": "", "approved_at": None}})
    result = call(service, approval_task_id="task-1")
    assert result.code == "approval_not_durably_approved"
    assert provider.calls == 0
    assert rate.calls == []
def test_service_rejects_approval_bound_to_different_request():
    provider = FakeProvider()
    service, rate, _ = setup(provider, {"task-1": approved_record()})
    result = call(service, request_id="different-request", approval_task_id="task-1")
    assert result.code == "approval_not_durably_approved"
    assert provider.calls == 0
    assert rate.calls == []


def test_service_never_calls_adapter_for_unavailable_provider():
    provider = FakeProvider()
    provider.is_available = lambda: False
    service, rate, _ = setup(provider)
    result = call(service)
    assert result.code == "provider_unavailable"
    assert provider.calls == 0
    assert rate.calls == []

@pytest.mark.parametrize(
    ("mutate", "expected_code"),
    [
        (lambda provider: provider.config.update({"billing_mode": "paid_api"}), "paid_or_unverified_provider_blocked"),
        (lambda provider: provider.config.update({"cost_verified": False}), "paid_or_unverified_provider_blocked"),
        (lambda provider: provider.health_metrics.update({"quota_limit": None}), "cost_or_quota_unknown"),
        (lambda provider: provider.health_metrics.update({"quota_used": 10}), "free_quota_exhausted"),
    ],
)
def test_service_never_calls_provider_when_free_cost_or_quota_is_not_verified(mutate, expected_code):
    provider = FakeProvider()
    mutate(provider)
    service, rate, _ = setup(provider)

    result = call(service)

    assert result.success is False
    assert result.code == expected_code
    assert provider.calls == 0
    assert rate.calls == []


def test_service_blocks_provider_without_atomic_free_quota_reservation():
    provider = FakeProvider()
    provider.reserve_free_quota = None
    service, rate, _ = setup(provider)

    result = call(service)

    assert result.code == "free_quota_reservation_unavailable"
    assert provider.calls == 0
    assert rate.calls == ["provider-a"]
