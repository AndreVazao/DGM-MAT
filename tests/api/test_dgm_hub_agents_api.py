from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from core.api import dgm_hub_agents_api as api
from core.organization.dgm_hub_multichat_bridge import HubTaskResult


class FakeStore:
    def __init__(self):
        self.created = []
        self.records = {}

    def create_packet(self, **kwargs):
        item = {"collaboration_id": f"collab_{len(self.created) + 1}", **kwargs}
        self.created.append(item)
        self.records[item["collaboration_id"]] = SimpleNamespace(status=SimpleNamespace(value="PREPARED"))
        return item

    def get(self, collaboration_id):
        return self.records[collaboration_id]


class FakeEngine:
    def __init__(self):
        self.collaboration_store = FakeStore()
        self.results = []
        self.paused = []

    def record_specialist_result(self, collaboration_id, *, result, provenance):
        self.results.append((collaboration_id, result, provenance))
        self.collaboration_store.records[collaboration_id] = SimpleNamespace(
            status=SimpleNamespace(value="RESULT_RECEIVED")
        )
        return {
            "collaboration_id": collaboration_id,
            "status": "RESULT_RECEIVED",
            "review_required": True,
        }

    def pause_specialist_collaboration(self, collaboration_id, *, reason):
        self.paused.append((collaboration_id, reason))
        self.collaboration_store.records[collaboration_id] = SimpleNamespace(
            status=SimpleNamespace(value="WAITING_FOR_FREE_CAPACITY")
        )
        return {"collaboration_id": collaboration_id, "status": "WAITING_FOR_FREE_CAPACITY"}


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


def _payload(**overrides):
    value = {
        "goal": "Review the DGM-MAT provider integration.",
        "context": "The DGM-HUB room is already configured on loopback.",
        "providers": ["codex", "claude"],
        "free_capacity_confirmed": True,
    }
    value.update(overrides)
    return api.HubAgentConsultRequest(**value)


def test_consult_requires_explicit_free_capacity_attestation(monkeypatch):
    bridge = FakeBridge()
    engine = FakeEngine()
    monkeypatch.setattr(api, "_bridge", lambda: bridge)
    monkeypatch.setattr(api, "_mission_engine", lambda: engine)

    with pytest.raises(HTTPException) as exc:
        api.consult_hub_agents(_payload(free_capacity_confirmed=False))

    assert exc.value.status_code == 400
    assert bridge.called == []
    assert engine.collaboration_store.created == []


def test_consult_persists_each_provider_result_as_untrusted_and_reviewable(monkeypatch):
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
    engine = FakeEngine()
    monkeypatch.setattr(api, "_bridge", lambda: bridge)
    monkeypatch.setattr(api, "_mission_engine", lambda: engine)

    result = api.consult_hub_agents(_payload())

    assert result["status"] == "completed"
    assert result["room_leader"] == "operator"
    assert result["dgm_mat_mode"] == "observer_and_consultation_coordinator"
    assert result["paid_fallback"] is False
    assert result["all_results_untrusted"] is True
    assert len(engine.collaboration_store.created) == 2
    assert len(engine.results) == 2
    assert all(item["review_required"] is True for item in result["providers"])
    assert all(item["result_trusted"] is False for item in result["providers"])
    assert "model_id=not-reported" in engine.results[0][2]
    assert bridge.called[0]["providers"] == ["codex", "claude"]


def test_consult_pauses_packets_when_hub_provider_is_unavailable(monkeypatch):
    bridge = FakeBridge(error=api.HubProviderUnavailable("claude not ready"))
    engine = FakeEngine()
    monkeypatch.setattr(api, "_bridge", lambda: bridge)
    monkeypatch.setattr(api, "_mission_engine", lambda: engine)

    with pytest.raises(HTTPException) as exc:
        api.consult_hub_agents(_payload())

    assert exc.value.status_code == 409
    assert len(engine.collaboration_store.created) == 2
    assert len(engine.paused) == 2
    assert engine.results == []


def test_consult_pauses_packets_on_hub_failure_without_retry_or_paid_fallback(monkeypatch):
    bridge = FakeBridge(error=api.HubBridgeError("Hub offline"))
    engine = FakeEngine()
    monkeypatch.setattr(api, "_bridge", lambda: bridge)
    monkeypatch.setattr(api, "_mission_engine", lambda: engine)

    with pytest.raises(HTTPException) as exc:
        api.consult_hub_agents(_payload())

    assert exc.value.status_code == 503
    assert len(engine.paused) == 2
    assert all("no retry or paid fallback" in reason for _, reason in engine.paused)


def test_failed_provider_result_is_not_promoted_as_a_validated_answer(monkeypatch):
    bridge = FakeBridge(
        task=HubTaskResult(
            task_id="hub-task-2",
            conversation_id="dgm-mat-room-2",
            results={
                "codex": {
                    "provider": "codex", "status": "rate_limited", "text": "",
                    "model": None, "duration_seconds": None, "truncated": False,
                }
            },
        )
    )
    engine = FakeEngine()
    monkeypatch.setattr(api, "_bridge", lambda: bridge)
    monkeypatch.setattr(api, "_mission_engine", lambda: engine)

    result = api.consult_hub_agents(_payload(providers=["codex"]))

    assert result["providers"][0]["status"] == "WAITING_FOR_FREE_CAPACITY"
    assert result["providers"][0]["review_required"] is False
    assert engine.results == []
    assert len(engine.paused) == 1


def test_secret_like_context_is_rejected_before_any_provider_call(monkeypatch):
    bridge = FakeBridge()
    engine = FakeEngine()
    monkeypatch.setattr(api, "_bridge", lambda: bridge)
    monkeypatch.setattr(api, "_mission_engine", lambda: engine)

    with pytest.raises(HTTPException) as exc:
        api.consult_hub_agents(
            _payload(context="api_key=sk-12345678901234567890123456789012")
        )

    assert exc.value.status_code == 422
    assert bridge.called == []
    assert engine.collaboration_store.created == []
