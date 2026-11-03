from __future__ import annotations

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from core.api import dgm_hub_agents_api as api
from core.conversation_intelligence.knowledge_store import ConversationKnowledgeStore
from core.conversation_intelligence.models import AIProposal
from core.organization.dgm_hub_meeting_observer import HubMeetingStore


def _request():
    request = Request({
        "type": "http",
        "method": "POST",
        "path": "/governance/agents/hub/meetings/room-1/decision",
        "headers": [],
        "query_string": b"",
        "server": ("127.0.0.1", 8181),
        "client": ("127.0.0.1", 12345),
        "scheme": "http",
    })
    request.state.dgm_principal = {
        "subject": "operator-test",
        "session_id": "session-test",
        "scopes": ["operator"],
    }
    return request


class FakeObserver:
    def __init__(self, store):
        self.store = store


def _meeting_store(tmp_path, monkeypatch):
    store = HubMeetingStore(tmp_path / "hub.sqlite3")
    events = [
        {
            "timestamp": "2026-11-03T11:00:00+00:00",
            "kind": "user_message",
            "conversation_id": "room-1",
            "message": "Vamos decidir a arquitetura.",
            "targets": ["llm7"],
        },
        {
            "timestamp": "2026-11-03T11:00:05+00:00",
            "kind": "provider_response",
            "conversation_id": "room-1",
            "provider": "llm7",
            "status": "ok",
            "text": "Proposta: separar observação da decisão.",
        },
    ]
    store.ingest(events)
    observer = FakeObserver(store)
    monkeypatch.setattr(api, "get_hub_meeting_observer", lambda: observer)
    return store, observer


def test_proposal_must_reference_provider_response_from_same_meeting(tmp_path, monkeypatch):
    store, _observer = _meeting_store(tmp_path, monkeypatch)
    user_event = next(
        item for item in store.get_meeting("room-1")["events"]
        if item["kind"] == "user_message"
    )

    with pytest.raises(HTTPException) as exc:
        api.record_hub_meeting_proposal(
            "room-1",
            api.HubMeetingProposalRequest(
                source_event_id=user_event["event_id"],
                statement="Separar observação e decisão.",
            ),
        )

    assert exc.value.status_code == 422


def test_proposal_is_linked_to_immutable_provider_event(tmp_path, monkeypatch):
    store, _observer = _meeting_store(tmp_path, monkeypatch)
    provider_event = next(
        item for item in store.get_meeting("room-1")["events"]
        if item["kind"] == "provider_response"
    )

    result = api.record_hub_meeting_proposal(
        "room-1",
        api.HubMeetingProposalRequest(
            source_event_id=provider_event["event_id"],
            statement="Separar observação e decisão.",
        ),
    )

    knowledge = ConversationKnowledgeStore(store.database_path)
    saved = knowledge.list_proposals()[0]
    assert result["proposal_id"] == saved["proposal_id"]
    assert saved["source_conversation_id"] == "room-1"
    assert saved["source_message_id"] == provider_event["event_id"]
    assert saved["accepted"] is None


def test_decision_requires_explicit_confirmation(tmp_path, monkeypatch):
    _store, _observer = _meeting_store(tmp_path, monkeypatch)
    payload = api.HubMeetingDecisionRequest(
        statement="Separar observação e decisão.",
        outcome="approved",
        rationale="Mantém a sala independente e a memória rastreável.",
        confirm=False,
    )

    with pytest.raises(HTTPException) as exc:
        api.record_hub_meeting_decision("room-1", payload, _request())

    assert exc.value.status_code == 400


def test_confirmed_decision_records_operator_rationale_and_rejected_alternative(tmp_path, monkeypatch):
    store, _observer = _meeting_store(tmp_path, monkeypatch)
    knowledge = ConversationKnowledgeStore(store.database_path)
    provider_event = next(
        item for item in store.get_meeting("room-1")["events"]
        if item["kind"] == "provider_response"
    )
    accepted = AIProposal(
        proposal_id="proposal-accepted",
        statement="Separar observação e decisão.",
        source_conversation_id="room-1",
        source_message_id=provider_event["event_id"],
    )
    rejected = AIProposal(
        proposal_id="proposal-rejected",
        statement="Dar liderança imediata ao DGM-MAT.",
        source_conversation_id="room-1",
        source_message_id=provider_event["event_id"],
    )
    knowledge.save_proposal(accepted)
    knowledge.save_proposal(rejected)

    result = api.record_hub_meeting_decision(
        "room-1",
        api.HubMeetingDecisionRequest(
            statement="Implementar primeiro o observador passivo.",
            outcome="approved",
            rationale="Precisamos de evidência real antes de delegar liderança.",
            accepted_proposal_ids=[accepted.proposal_id],
            rejected_proposal_ids=[rejected.proposal_id],
            confirm=True,
        ),
        _request(),
    )

    saved = knowledge.get_decision(result["decision_id"])
    assert saved is not None
    assert saved["confirmed_by_user"] is True
    assert saved["status"] == "confirmed"
    assert saved["source_conversation_id"] == "room-1"
    assert "rejected_proposal_id:proposal-rejected" in saved["evidence"]
    assert "accepted_proposal_id:proposal-accepted" in saved["evidence"]
    assert "operator_session_id:session-test" in saved["evidence"]
    reviewed = {item["proposal_id"]: item for item in knowledge.list_proposals()}
    assert reviewed[accepted.proposal_id]["accepted"] is True
    assert reviewed[accepted.proposal_id]["decision_id"] == result["decision_id"]
    assert reviewed[rejected.proposal_id]["accepted"] is False
    assert reviewed[rejected.proposal_id]["decision_id"] == result["decision_id"]


def test_decision_rejects_proposal_from_another_meeting(tmp_path, monkeypatch):
    store, _observer = _meeting_store(tmp_path, monkeypatch)
    knowledge = ConversationKnowledgeStore(store.database_path)
    knowledge.save_proposal(AIProposal(
        proposal_id="foreign-proposal",
        statement="Other meeting proposal.",
        source_conversation_id="another-room",
    ))

    with pytest.raises(HTTPException) as exc:
        api.record_hub_meeting_decision(
            "room-1",
            api.HubMeetingDecisionRequest(
                statement="Approve current proposal.",
                outcome="approved",
                rationale="Explicit operator choice.",
                accepted_proposal_ids=["foreign-proposal"],
                confirm=True,
            ),
            _request(),
        )

    assert exc.value.status_code == 422