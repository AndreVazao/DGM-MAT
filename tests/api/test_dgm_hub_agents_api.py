from __future__ import annotations

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from core.api import dgm_hub_agents_api as api
from core.organization.dgm_hub_multichat_bridge import HubTaskResult
from core.organization.specialist_collaboration import SpecialistCollaborationStore


class FakeEngine:
    def __init__(self, root):
        self.collaboration_store = SpecialistCollaborationStore(root)
        self.results = []
        self.paused = []

    def record_specialist_result(self, collaboration_id, *, result, provenance):
        packet = self.collaboration_store.record_result(
            collaboration_id, result=result, provenance=provenance
        )
        self.results.append((collaboration_id, result, provenance))
        return {
            "collaboration_id": collaboration_id,
            "status": packet.status.value,
            "review_required": True,
        }

    def pause_specialist_collaboration(self, collaboration_id, *, reason):
        packet = self.collaboration_store.mark_waiting_for_free_capacity(
            collaboration_id, reason=reason
        )
        self.paused.append((collaboration_id, reason))
        return {"collaboration_id": collaboration_id, "status": packet.status.value}


class FakeBridge:
    def __init__(self, task=None, error=None):
        self.task = task
        self.error = error
        self.called = []

    def get_status(self):
        return {"hub": "online", "providers": {}}

    def consult(self, **kwargs):
        self.called.append(kwargs)
        if self.error:
            raise self.error
        return self.task


@pytest.fixture(autouse=True)
def _default_audit(monkeypatch):
    monkeypatch.setattr(api, "append_command_audit", lambda **kwargs: None)


def _request():
    request = Request({
        "type": "http",
        "method": "POST",
        "path": "/governance/agents/hub/consult",
        "headers": [],
        "query_string": b"",
        "server": ("127.0.0.1", 8181),
        "client": ("127.0.0.1", 12345),
        "scheme": "http",
    })
    request.state.dgm_principal = {"session_id": "unit-test-session"}
    return request


def _payload(**overrides):
    value = {
        "goal": "Review the DGM-MAT provider integration.",
        "context": "The DGM-HUB room is already configured on loopback.",
        "providers": ["codex", "claude"],
        "free_capacity_confirmed": True,
    }
    value.update(overrides)
    return api.HubAgentConsultRequest(**value)


def test_consult_requires_explicit_free_capacity_attestation(monkeypatch, tmp_path):
    bridge = FakeBridge()
    engine = FakeEngine(tmp_path)
    monkeypatch.setattr(api, "_bridge", lambda: bridge)
    monkeypatch.setattr(api, "_mission_engine", lambda: engine)

    with pytest.raises(HTTPException) as exc:
        api.consult_hub_agents(_payload(free_capacity_confirmed=False), _request())

    assert exc.value.status_code == 400
    assert bridge.called == []
    assert engine.collaboration_store.list_packets() == []


def test_consult_persists_each_provider_result_as_untrusted_and_reviewable(monkeypatch, tmp_path):
    bridge = FakeBridge(
        task=HubTaskResult(
            task_id="hub-task-1",
            conversation_id="dgm-mat-room-1",
            results={
                "codex": {
                    "provider": "codex", "status": "ok", "text": "Codex review",
                    "model": None, "duration_seconds": 4.2, "truncated": False,
                },
                "claude": {
                    "provider": "claude", "status": "ok", "text": "Claude review",
                    "model": None, "duration_seconds": 5.1, "truncated": False,
                },
            },
        )
    )
    engine = FakeEngine(tmp_path)
    monkeypatch.setattr(api, "_bridge", lambda: bridge)
    monkeypatch.setattr(api, "_mission_engine", lambda: engine)

    result = api.consult_hub_agents(_payload(), _request())

    assert result["status"] == "completed"
    assert result["provider_count"] == 2
    assert result["successful_count"] == 2
    assert result["paused_count"] == 0
    assert result["room_leader"] == "operator"
    assert result["dgm_mat_mode"] == "observer_operator_requested_consultations"
    assert result["paid_fallback"] is False
    assert result["all_results_untrusted"] is True
    assert len(engine.collaboration_store.list_packets()) == 2
    assert len(engine.results) == 2
    assert all(item["review_required"] is True for item in result["providers"])
    assert all(item["result_trusted"] is False for item in result["providers"])
    assert "transport_model_id=not-reported" in engine.results[0][2]
    assert bridge.called[0]["providers"] == ["codex", "claude"]


def test_consult_pauses_packets_when_hub_provider_is_unavailable(monkeypatch, tmp_path):
    bridge = FakeBridge(error=api.HubProviderUnavailable("claude not ready"))
    engine = FakeEngine(tmp_path)
    monkeypatch.setattr(api, "_bridge", lambda: bridge)
    monkeypatch.setattr(api, "_mission_engine", lambda: engine)

    with pytest.raises(HTTPException) as exc:
        api.consult_hub_agents(_payload(), _request())

    assert exc.value.status_code == 409
    assert len(engine.collaboration_store.list_packets()) == 2
    assert len(engine.paused) == 2
    assert engine.results == []


def test_consult_pauses_packets_on_hub_failure_without_retry_or_paid_fallback(monkeypatch, tmp_path):
    bridge = FakeBridge(error=api.HubBridgeError("Hub offline"))
    engine = FakeEngine(tmp_path)
    monkeypatch.setattr(api, "_bridge", lambda: bridge)
    monkeypatch.setattr(api, "_mission_engine", lambda: engine)

    with pytest.raises(HTTPException) as exc:
        api.consult_hub_agents(_payload(), _request())

    assert exc.value.status_code == 503
    assert len(engine.paused) == 2
    assert all("no retry or paid fallback" in reason for _, reason in engine.paused)


def test_failed_provider_result_is_partial_and_not_promoted_as_validated(monkeypatch, tmp_path):
    bridge = FakeBridge(
        task=HubTaskResult(
            task_id="hub-task-2",
            conversation_id="dgm-mat-room-2",
            results={
                "codex": {
                    "provider": "codex", "status": "timeout", "text": "",
                    "model": None, "duration_seconds": None, "truncated": False,
                }
            },
        )
    )
    engine = FakeEngine(tmp_path)
    monkeypatch.setattr(api, "_bridge", lambda: bridge)
    monkeypatch.setattr(api, "_mission_engine", lambda: engine)

    result = api.consult_hub_agents(_payload(providers=["codex"]), _request())

    assert result["status"] == "partial"
    assert result["provider_count"] == 1
    assert result["successful_count"] == 0
    assert result["paused_count"] == 1
    assert result["providers"][0]["status"] == "PROVIDER_TIMEOUT"
    assert result["providers"][0]["provider_status"] == "timeout"
    assert result["providers"][0]["retry_attempted"] is False
    assert result["providers"][0]["review_required"] is False
    assert engine.results == []
    packet = engine.collaboration_store.list_packets()[0]
    assert packet.status.value == "PAUSED"
    assert "provider_message=not supplied" in packet.blocked_reason
    assert engine.paused == []



def test_rate_limit_remains_waiting_for_free_capacity_not_generic_failure(monkeypatch, tmp_path):
    bridge = FakeBridge(
        task=HubTaskResult(
            task_id="hub-task-rate-limit",
            conversation_id="dgm-mat-room-rate-limit",
            results={
                "llm7": {
                    "provider": "llm7", "status": "rate_limited",
                    "text": "Free request capacity exhausted.",
                    "model": "gpt-oss:20b", "duration_seconds": 2.0, "truncated": False,
                }
            },
        )
    )
    engine = FakeEngine(tmp_path)
    monkeypatch.setattr(api, "_bridge", lambda: bridge)
    monkeypatch.setattr(api, "_mission_engine", lambda: engine)

    result = api.consult_hub_agents(_payload(providers=["llm7"]), _request())

    assert result["status"] == "partial"
    assert result["providers"][0]["status"] == "WAITING_FOR_FREE_CAPACITY"
    assert result["providers"][0]["message"] == "Free request capacity exhausted."
    packet = engine.collaboration_store.list_packets()[0]
    assert packet.status.value == "WAITING_FOR_FREE_CAPACITY"
    assert len(engine.paused) == 1


def test_other_provider_errors_are_reported_as_provider_failures(monkeypatch, tmp_path):
    bridge = FakeBridge(
        task=HubTaskResult(
            task_id="hub-task-error",
            conversation_id="dgm-mat-room-error",
            results={
                "claude": {
                    "provider": "claude", "status": "error",
                    "text": "CLI process exited unexpectedly.",
                    "model": None, "duration_seconds": 3.0, "truncated": False,
                }
            },
        )
    )
    engine = FakeEngine(tmp_path)
    monkeypatch.setattr(api, "_bridge", lambda: bridge)
    monkeypatch.setattr(api, "_mission_engine", lambda: engine)

    result = api.consult_hub_agents(_payload(providers=["claude"]), _request())

    assert result["status"] == "partial"
    assert result["providers"][0]["status"] == "PROVIDER_FAILED"
    assert result["providers"][0]["message"] == "CLI process exited unexpectedly."
    assert engine.collaboration_store.list_packets()[0].status.value == "PAUSED"
    assert engine.paused == []

def test_secret_like_context_is_rejected_before_any_provider_call(monkeypatch, tmp_path):
    bridge = FakeBridge()
    engine = FakeEngine(tmp_path)
    monkeypatch.setattr(api, "_bridge", lambda: bridge)
    monkeypatch.setattr(api, "_mission_engine", lambda: engine)

    with pytest.raises(HTTPException) as exc:
        api.consult_hub_agents(
            _payload(context="api_key=sk-12345678901234567890123456789012"), _request()
        )

    assert exc.value.status_code == 422
    assert bridge.called == []
    assert engine.collaboration_store.list_packets() == []


def test_consult_audits_operator_and_provider_selection_before_and_after_call(monkeypatch, tmp_path):
    events = []
    monkeypatch.setattr(api, "append_command_audit", lambda **kwargs: events.append(kwargs))
    bridge = FakeBridge(
        task=HubTaskResult(
            task_id="audit-task",
            conversation_id="audit-conversation",
            results={
                "llm7": {
                    "provider": "llm7", "status": "ok", "text": "Audited result",
                    "model": "gpt-oss:20b", "duration_seconds": 1.0, "truncated": False,
                }
            },
        )
    )
    engine = FakeEngine(tmp_path)
    monkeypatch.setattr(api, "_bridge", lambda: bridge)
    monkeypatch.setattr(api, "_mission_engine", lambda: engine)

    result = api.consult_hub_agents(_payload(providers=["llm7"]), _request())

    assert result["status"] == "completed"
    assert [event["event"] for event in events] == ["command.requested", "command.completed"]
    assert all(event["session_id"] == "unit-test-session" for event in events)
    assert all(event["command_id"] == "dgm_hub.consult.free_only:llm7" for event in events)
    assert events[0]["status"] == "requested"
    assert events[1]["status"] == "completed"
    assert events[1]["duration_ms"] is not None


def test_consult_fails_closed_when_request_audit_cannot_be_written(monkeypatch, tmp_path):
    bridge = FakeBridge()
    engine = FakeEngine(tmp_path)
    monkeypatch.setattr(api, "_bridge", lambda: bridge)
    monkeypatch.setattr(api, "_mission_engine", lambda: engine)

    def fail_audit(**kwargs):
        raise api.AuditWriteError("audit unavailable")

    monkeypatch.setattr(api, "append_command_audit", fail_audit)

    with pytest.raises(HTTPException) as exc:
        api.consult_hub_agents(_payload(providers=["llm7"]), _request())

    assert exc.value.status_code == 503
    assert bridge.called == []
    assert engine.collaboration_store.list_packets() == []

def test_consult_rejects_duplicate_provider_ids_before_provider_contact(monkeypatch, tmp_path):
    events = []
    bridge = FakeBridge()
    engine = FakeEngine(tmp_path)
    monkeypatch.setattr(api, "append_command_audit", lambda **kwargs: events.append(kwargs))
    monkeypatch.setattr(api, "_bridge", lambda: bridge)
    monkeypatch.setattr(api, "_mission_engine", lambda: engine)

    with pytest.raises(HTTPException) as exc:
        api.consult_hub_agents(_payload(providers=["llm7", "llm7"]), _request())

    assert exc.value.status_code == 422
    assert bridge.called == []
    assert engine.collaboration_store.list_packets() == []
    assert [event["event"] for event in events] == ["command.denied"]
    assert events[0]["status"] == "denied"
