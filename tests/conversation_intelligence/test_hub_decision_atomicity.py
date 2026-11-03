from __future__ import annotations

import pytest

from core.conversation_intelligence.knowledge_store import ConversationKnowledgeStore
from core.conversation_intelligence.models import AIProposal, UserDecision


def _decision():
    return UserDecision(
        decision_id="hub-decision-atomic",
        statement="Approved: begin with passive observation.",
        status="confirmed",
        source_conversation_id="hub-room",
        decided_at="2026-11-03T11:00:00+00:00",
        evidence=["operator-confirmed", "rationale:observe before leading"],
        confirmed_by_user=True,
    )


def test_decision_and_proposal_reviews_commit_atomically(tmp_path):
    store = ConversationKnowledgeStore(tmp_path / "knowledge.sqlite3")
    store.save_proposal(AIProposal(
        proposal_id="proposal-accept",
        statement="Use a passive event observer.",
        source_conversation_id="hub-room",
    ))
    store.save_proposal(AIProposal(
        proposal_id="proposal-reject",
        statement="Let DGM-MAT lead immediately.",
        source_conversation_id="hub-room",
    ))

    store.save_decision_with_proposals(
        _decision(),
        accepted_proposal_ids=["proposal-accept"],
        rejected_proposal_ids=["proposal-reject"],
    )

    proposals = {item["proposal_id"]: item for item in store.list_proposals()}
    assert store.get_decision("hub-decision-atomic")["confirmed_by_user"] is True
    assert proposals["proposal-accept"]["accepted"] is True
    assert proposals["proposal-accept"]["decision_id"] == "hub-decision-atomic"
    assert proposals["proposal-reject"]["accepted"] is False
    assert proposals["proposal-reject"]["decision_id"] == "hub-decision-atomic"


def test_decision_and_proposal_reviews_roll_back_together_on_invalid_reference(tmp_path):
    store = ConversationKnowledgeStore(tmp_path / "knowledge.sqlite3")
    store.save_proposal(AIProposal(
        proposal_id="proposal-local",
        statement="Local proposal.",
        source_conversation_id="hub-room",
    ))
    store.save_proposal(AIProposal(
        proposal_id="proposal-foreign",
        statement="Foreign proposal.",
        source_conversation_id="other-room",
    ))

    with pytest.raises(ValueError):
        store.save_decision_with_proposals(
            _decision(),
            accepted_proposal_ids=["proposal-local"],
            rejected_proposal_ids=["proposal-foreign"],
        )

    assert store.get_decision("hub-decision-atomic") is None
    proposals = {item["proposal_id"]: item for item in store.list_proposals()}
    assert proposals["proposal-local"]["accepted"] is None
    assert proposals["proposal-local"]["decision_id"] is None


def test_confirmed_proposal_review_cannot_be_rewritten(tmp_path):
    store = ConversationKnowledgeStore(tmp_path / "knowledge.sqlite3")
    store.save_proposal(AIProposal(
        proposal_id="proposal-once",
        statement="First proposal.",
        source_conversation_id="hub-room",
    ))
    store.save_decision_with_proposals(
        _decision(), accepted_proposal_ids=["proposal-once"]
    )

    changed = UserDecision(
        decision_id="hub-decision-second",
        statement="A different decision.",
        status="confirmed",
        source_conversation_id="hub-room",
        decided_at="2026-11-03T11:05:00+00:00",
        evidence=["new rationale"],
        confirmed_by_user=True,
    )
    with pytest.raises(ValueError):
        store.save_decision_with_proposals(
            changed, rejected_proposal_ids=["proposal-once"]
        )

    assert store.get_decision("hub-decision-second") is None
    assert store.list_proposals()[0]["accepted"] is True



def test_unconfirmed_decision_cannot_accept_or_reject_agent_proposals(tmp_path):
    store = ConversationKnowledgeStore(tmp_path / "knowledge.sqlite3")
    store.save_proposal(AIProposal(
        proposal_id="proposal-unconfirmed",
        statement="Candidate suggestion.",
        source_conversation_id="hub-room",
    ))
    decision = _decision()
    decision.status = "unverified"
    decision.confirmed_by_user = False

    with pytest.raises(ValueError, match="explicitly user-confirmed"):
        store.save_decision_with_proposals(
            decision, accepted_proposal_ids=["proposal-unconfirmed"]
        )

    assert store.get_decision(decision.decision_id) is None
    assert store.list_proposals()[0]["accepted"] is None