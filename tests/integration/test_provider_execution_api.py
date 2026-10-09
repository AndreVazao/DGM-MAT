# Path: C:\ProgramasGodMode\DGM-MAT\tests\integration\test_provider_execution_api.py
from datetime import datetime
from fastapi.testclient import TestClient

from core.api.api_server import app
from core.api import provider_execution_api as api
from core.provider_sync.governed_provider_service import GovernedProviderService
from core.provider_sync.provider_request_policy import ProviderRequestPolicy
from core.governance.provider_rate_control import ProviderRateControl
from core.providers.base.provider_base import ProviderBase


class FakeProvider(ProviderBase):
    def __init__(self):
        super().__init__("api-test-provider")
        self.health_metrics["last_check"] = 1
        self.health_metrics["status"] = "ok"
        self.health_metrics["quota_used"] = 0
        self.health_metrics["quota_limit"] = 10
        self.capabilities["cost_profile"] = "free"
        self.config.update({"billing_mode": "free_tier", "cost_verified": True})
        self.calls = 0

    def reserve_free_quota(self):
        used = self.health_metrics["quota_used"]
        limit = self.health_metrics["quota_limit"]
        if used >= limit:
            return False
        self.health_metrics["quota_used"] = used + 1
        return True

    async def chat(self, messages, **kwargs):
        self.calls += 1
        return "safe test response"


class FakeQueue:
    def __init__(self, store):
        self.store = store

    def list_pending_approvals(self):
        return [
            dict(item)
            for item in self.store.records.values()
            if item["status"] == "QUEUED"
        ]

    def approve_approval(self, task_id, operator="manual"):
        item = self.store.records.get(task_id)
        if not item or item["status"] != "QUEUED":
            return False
        item["status"] = "APPROVED"
        item["approved_by"] = operator
        item["approved_at"] = datetime.now().isoformat()
        item["is_approved"] = False
        return True

    def reject_approval(self, task_id, reason="", operator="manual"):
        item = self.store.records.get(task_id)
        if not item or item["status"] != "QUEUED":
            return False
        item["status"] = "REJECTED"
        item["error_message"] = reason
        item["approved_by"] = operator
        return True


class FakeStore:
    def __init__(self):
        self.records = {}
        self._queue = FakeQueue(self)

    def request_provider_approval(self, **kwargs):
        task_id = kwargs["task_id"]
        self.records[task_id] = {
            "id": len(self.records) + 1,
            "action_type": "APPROVAL_REQUEST",
            "status": "QUEUED",
            "is_approved": False,
            "approved_by": None,
            "approved_at": None,
            "created_at": datetime.now().isoformat(),
            "payload": {
                "task_id": task_id,
                "provider_request_fingerprint": kwargs["provider_request_fingerprint"],
                "diff": kwargs["summary"],
                "provider_id": kwargs["provider_id"],
                "request_id": kwargs["request_id"],
                "messages": kwargs["messages"],
            },
        }
        return self.records[task_id]["id"]

    def get_approval(self, task_id):
        item = self.records.get(task_id)
        if not item:
            return None
        result = dict(item)
        result["provider_request_fingerprint"] = item["payload"].get("provider_request_fingerprint")
        return result

    def claim_approval(self, task_id, expected_fingerprint):
        item = self.records.get(task_id)
        if not item or item["status"] != "APPROVED":
            return False
        if item["payload"]["provider_request_fingerprint"] != expected_fingerprint:
            return False
        item["status"] = "RUNNING"
        return True

    def record_execution_outcome(self, task_id, *, success, code, elapsed_ms):
        item = self.records.get(task_id)
        if not item or item["status"] != "RUNNING":
            return False
        item["status"] = "COMPLETED" if success else "FAILED"
        item["execution_code"] = code
        return True


def setup_api(monkeypatch):
    monkeypatch.setenv("DGM_PROVIDER_API_TOKEN", "test-api-token")
    monkeypatch.setenv("DGM_PROVIDER_OPERATOR_TOKEN", "test-operator-token")
    monkeypatch.setenv("DGM_PROVIDER_OPERATOR_ID", "test-operator")
    store = FakeStore()
    provider = FakeProvider()
    api.provider_registry._providers.pop(provider.name, None)
    api.provider_registry.register(provider.name, provider)
    monkeypatch.setattr(api, "_get_approval_store", lambda: store)
    monkeypatch.setattr(
        api,
        "_get_provider_service",
        lambda: GovernedProviderService(
            ProviderRequestPolicy(api.provider_registry, ProviderRateControl(10)),
            store,
            timeout_seconds=1,
        ),
    )
    return TestClient(app), store, provider


def test_provider_api_fails_closed_when_tokens_are_not_configured(monkeypatch):
    monkeypatch.delenv("DGM_PROVIDER_API_TOKEN", raising=False)
    monkeypatch.delenv("DGM_PROVIDER_OPERATOR_TOKEN", raising=False)
    client = TestClient(app)
    response = client.post("/provider-execution/requests", json={
        "provider_id": "api-test-provider",
        "request_id": "req-1",
        "messages": [{"role": "user", "content": "hello"}],
    })
    assert response.status_code == 503


def test_provider_api_requires_separate_credentials(monkeypatch):
    monkeypatch.setenv("DGM_PROVIDER_API_TOKEN", "same-token")
    monkeypatch.setenv("DGM_PROVIDER_OPERATOR_TOKEN", "same-token")
    response = TestClient(app).get(
        "/provider-execution/approvals",
        headers={"Authorization": "Bearer same-token"},
    )
    assert response.status_code == 503


def test_provider_api_request_approval_and_execute_happy_path(monkeypatch):
    client, store, provider = setup_api(monkeypatch)
    body = {
        "provider_id": "api-test-provider",
        "request_id": "req-100",
        "messages": [{"role": "user", "content": "please answer safely"}],
    }
    api_headers = {"Authorization": "Bearer test-api-token"}
    operator_headers = {"Authorization": "Bearer test-operator-token"}

    unauthenticated = client.post("/provider-execution/requests", json=body)
    assert unauthenticated.status_code == 401
    assert store.records == {}

    created = client.post("/provider-execution/requests", json=body, headers=api_headers)
    assert created.status_code == 201
    task_id = created.json()["approval_task_id"]
    assert created.json()["status"] == "awaiting_approval"
    assert provider.calls == 0

    wrong_role = client.get("/provider-execution/approvals", headers=api_headers)
    assert wrong_role.status_code == 401

    pending = client.get("/provider-execution/approvals", headers=operator_headers)
    assert pending.status_code == 200
    assert pending.json()["approvals"][0]["messages"] == body["messages"]

    approved = client.post(
        f"/provider-execution/approvals/{task_id}/decision",
        json={"decision": "approve"},
        headers=operator_headers,
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"

    executed = client.post(
        "/provider-execution/execute",
        json={"approval_task_id": task_id},
        headers=api_headers,
    )
    assert executed.status_code == 200
    assert executed.json()["response"] == "safe test response"
    assert provider.calls == 1
    assert store.records[task_id]["status"] == "COMPLETED"

    replay = client.post(
        "/provider-execution/execute",
        json={"approval_task_id": task_id},
        headers=api_headers,
    )
    assert replay.status_code == 409
    assert provider.calls == 1
    api.provider_registry._providers.pop(provider.name, None)


def test_provider_api_rejects_execution_when_approved_envelope_was_changed(monkeypatch):
    client, store, provider = setup_api(monkeypatch)
    headers = {"Authorization": "Bearer test-api-token"}
    operator_headers = {"Authorization": "Bearer test-operator-token"}
    created = client.post("/provider-execution/requests", headers=headers, json={
        "provider_id": "api-test-provider",
        "request_id": "req-101",
        "messages": [{"role": "user", "content": "original content"}],
    })
    assert created.status_code == 201
    task_id = created.json()["approval_task_id"]
    assert client.post(
        f"/provider-execution/approvals/{task_id}/decision",
        headers=operator_headers,
        json={"decision": "approve"},
    ).status_code == 200
    store.records[task_id]["payload"]["messages"] = [{"role": "user", "content": "tampered content"}]
    executed = client.post(
        "/provider-execution/execute",
        headers=headers,
        json={"approval_task_id": task_id},
    )
    assert executed.status_code == 409
    assert provider.calls == 0
    api.provider_registry._providers.pop(provider.name, None)


def test_provider_api_rejects_extra_message_fields(monkeypatch):
    client, store, provider = setup_api(monkeypatch)
    response = client.post(
        "/provider-execution/requests",
        headers={"Authorization": "Bearer test-api-token"},
        json={
            "provider_id": "api-test-provider",
            "request_id": "req-102",
            "messages": [{"role": "user", "content": "hello", "tool_calls": [{"name": "run"}]}],
        },
    )
    assert response.status_code == 422
    assert store.records == {}
    assert provider.calls == 0
    api.provider_registry._providers.pop(provider.name, None)
