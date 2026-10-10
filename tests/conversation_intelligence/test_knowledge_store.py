from __future__ import annotations

import pytest

from core.conversation_intelligence.knowledge_store import ConversationKnowledgeStore
from core.conversation_intelligence.models import AIProposal, ConversationRelation, UserDecision, UserIntent


def test_intents_proposals_decisions_and_relations_survive_reopen(tmp_path):
    database = tmp_path / "knowledge.sqlite3"
    store = ConversationKnowledgeStore(database)
    store.save_intent(UserIntent(
        intent_id="intent-1",
        statement="Recover and classify existing AI conversations first",
        source_conversation_id="conv-1",
        source_message_id="msg-user-1",
        evidence=["conv-1#msg-user-1"],
        confidence=1.0,
    ))
    store.save_proposal(AIProposal(
        proposal_id="proposal-1",
        statement="Use a persistent SQLite ledger",
        source_conversation_id="conv-2",
        source_message_id="msg-ai-4",
    ))
    store.save_decision(UserDecision(
        decision_id="decision-1",
        statement="Do not reread unchanged completed conversations",
        status="confirmed",
        source_conversation_id="conv-3",
        source_message_id="msg-user-9",
        evidence=["conv-3#msg-user-9"],
        confirmed_by_user=True,
    ))
    store.save_relation(ConversationRelation(
        relation_id="relation-1",
        source_conversation_id="conv-1",
        target_conversation_id="conv-3",
        relation_type="continues",
        evidence=["shared project and explicit continuation"],
        confidence=0.95,
    ))

    reopened = ConversationKnowledgeStore(database)
    assert reopened.get_intent("intent-1")["status"] == "unverified"
    assert reopened.get_intent("intent-1")["evidence"] == ["conv-1#msg-user-1"]
    assert reopened.get_decision("decision-1")["confirmed_by_user"] is True
    assert reopened.list_relations("conv-3")[0]["relation_type"] == "continues"
    assert reopened.summary() == {
        "intents": 1, "proposals": 1, "decisions": 1, "relations": 1,
        "review_tasks": 0, "review_tasks_open": 0,
    }


def test_reviewed_intent_cannot_be_silently_changed(tmp_path):
    store = ConversationKnowledgeStore(tmp_path / "knowledge.sqlite3")
    confirmed = UserIntent(
        intent_id="intent-reviewed",
        statement="Use incremental imports",
        status="confirmed",
        evidence=["conv-1#msg-2"],
        confidence=1.0,
        reviewed_by_user=True,
    )
    store.save_intent(confirmed)
    store.save_intent(confirmed)  # exact repeat is idempotent

    with pytest.raises(ValueError, match="Reviewed intent is immutable"):
        store.save_intent(UserIntent(
            intent_id="intent-reviewed",
            statement="Reread every conversation every run",
            status="current",
            confidence=0.8,
            reviewed_by_user=False,
        ))
    assert store.get_intent("intent-reviewed")["statement"] == "Use incremental imports"


def test_confirmed_user_decision_cannot_be_silently_replaced(tmp_path):
    store = ConversationKnowledgeStore(tmp_path / "knowledge.sqlite3")
    decision = UserDecision(
        decision_id="decision-reviewed",
        statement="Stability before features",
        status="confirmed",
        evidence=["conv-4#msg-2"],
        confirmed_by_user=True,
    )
    store.save_decision(decision)
    with pytest.raises(ValueError, match="User-confirmed decision is immutable"):
        store.save_decision(UserDecision(
            decision_id="decision-reviewed",
            statement="Ship features without validation",
            status="unverified",
        ))
    assert store.get_decision("decision-reviewed")["status"] == "confirmed"


def test_ai_proposal_is_not_a_user_decision_and_acceptance_is_preserved(tmp_path):
    store = ConversationKnowledgeStore(tmp_path / "knowledge.sqlite3")
    store.save_proposal(AIProposal(
        proposal_id="proposal",
        statement="Move all conversations to provider folders",
        source_conversation_id="conv-ai",
    ))
    assert store.summary()["proposals"] == 1
    assert store.summary()["decisions"] == 0
    store.save_proposal(AIProposal(
        proposal_id="proposal",
        statement="Move all conversations to provider folders",
        source_conversation_id="conv-ai",
        accepted=True,
        decision_id="decision-explicit",
    ))
    with pytest.raises(ValueError, match="cannot be silently rewritten"):
        store.save_proposal(AIProposal(
            proposal_id="proposal",
            statement="Move all conversations to provider folders",
            source_conversation_id="conv-ai",
            accepted=False,
        ))
    with pytest.raises(ValueError, match="cannot be silently rewritten"):
        store.save_proposal(AIProposal(
            proposal_id="proposal",
            statement="Silently change the accepted proposal text",
            source_conversation_id="conv-ai",
            accepted=True,
        ))


def test_relation_rejects_self_link_and_preserves_reviewed_relation(tmp_path):
    store = ConversationKnowledgeStore(tmp_path / "knowledge.sqlite3")
    with pytest.raises(ValueError, match="cannot be related to itself"):
        store.save_relation(ConversationRelation(
            relation_id="self", source_conversation_id="same", target_conversation_id="same",
            relation_type="continues",
        ))
    reviewed = ConversationRelation(
        relation_id="relation-reviewed", source_conversation_id="conv-a", target_conversation_id="conv-b",
        relation_type="same_project", evidence=["explicit project marker"], confidence=1.0,
        reviewed_by_user=True,
    )
    store.save_relation(reviewed)
    store.save_relation(reviewed)
    with pytest.raises(ValueError, match="Reviewed relation is immutable"):
        store.save_relation(ConversationRelation(
            relation_id="relation-reviewed", source_conversation_id="conv-a", target_conversation_id="conv-c",
            relation_type="continues", confidence=0.7,
        ))


def test_review_task_is_resolved_independently_of_conversation_import(tmp_path):
    store = ConversationKnowledgeStore(tmp_path / "knowledge.sqlite3")
    task = store.create_review_task(
        task_id="review-1",
        item_type="decision",
        item_id="decision-pending",
        reason="Confirm whether a later request supersedes the earlier one",
        evidence=["conv-7#msg-user-8"],
    )
    assert task["status"] == "open"
    assert store.list_open_review_tasks()[0]["task_id"] == "review-1"
    assert store.resolve_review_task(
        "review-1",
        resolution="Later user message supersedes the earlier technical approach",
        evidence=["conv-7#msg-user-8", "conv-7#msg-user-12"],
    )
    assert not store.resolve_review_task(
        "review-1", resolution="duplicate", evidence=["conv-7#msg-user-12"]
    )
    assert store.list_open_review_tasks() == []
    assert store.summary()["review_tasks_open"] == 0


def test_invalid_confidence_and_missing_evidence_resolution_are_rejected(tmp_path):
    store = ConversationKnowledgeStore(tmp_path / "knowledge.sqlite3")
    with pytest.raises(ValueError, match="confidence"):
        store.save_intent(UserIntent(intent_id="bad", statement="x", confidence=1.1))
    with pytest.raises(ValueError, match="resolution and evidence"):
        store.resolve_review_task("missing", resolution="done", evidence=[])



def test_knowledge_changes_keep_temporal_snapshots(tmp_path):
    store = ConversationKnowledgeStore(tmp_path / "knowledge.sqlite3")
    store.save_intent(UserIntent(
        intent_id="evolving-intent",
        statement="Initial direction",
        evidence=["conv-1#msg-1"],
    ))
    store.save_intent(UserIntent(
        intent_id="evolving-intent",
        statement="Initial direction",
        evidence=["conv-1#msg-1"],
    ))  # identical repeat must not create another history event
    store.save_intent(UserIntent(
        intent_id="evolving-intent",
        statement="Later direction after new user instruction",
        evidence=["conv-2#msg-8"],
    ))

    history = store.history("intent", "evolving-intent")
    assert len(history) == 2
    assert history[0]["payload"]["statement"] == "Initial direction"
    assert history[1]["payload"]["statement"] == "Later direction after new user instruction"


def test_review_task_history_is_incremental_and_does_not_duplicate_creation(tmp_path):
    store = ConversationKnowledgeStore(tmp_path / "knowledge.sqlite3")
    args = dict(
        task_id="review-evolution",
        item_type="decision",
        item_id="decision-1",
        reason="Confirm which user instruction is current",
        evidence=["conv-4#msg-2"],
    )
    store.create_review_task(**args)
    store.create_review_task(**args)
    assert len(store.history("review_task", "review-evolution")) == 1

    assert store.resolve_review_task(
        "review-evolution",
        resolution="Later instruction supersedes the earlier approach",
        evidence=["conv-4#msg-2", "conv-4#msg-9"],
    )
    history = store.history("review_task", "review-evolution")
    assert [entry["event_type"] for entry in history] == ["created", "resolved"]
    assert history[1]["payload"]["status"] == "resolved"



def test_accepted_proposal_preserves_message_and_decision_provenance(tmp_path):
    store = ConversationKnowledgeStore(tmp_path / "knowledge.sqlite3")
    accepted = AIProposal(
        proposal_id="proposal-provenance",
        statement="Use the evidence-aware pipeline",
        source_conversation_id="conv-source",
        source_message_id="msg-original",
        accepted=True,
        decision_id="decision-original",
    )
    store.save_proposal(accepted)

    with pytest.raises(ValueError, match="cannot be silently rewritten"):
        store.save_proposal(AIProposal(
            proposal_id="proposal-provenance",
            statement="Use the evidence-aware pipeline",
            source_conversation_id="conv-source",
            source_message_id="msg-substituted",
            accepted=True,
            decision_id="decision-original",
        ))

    with pytest.raises(ValueError, match="cannot be silently rewritten"):
        store.save_proposal(AIProposal(
            proposal_id="proposal-provenance",
            statement="Use the evidence-aware pipeline",
            source_conversation_id="conv-source",
            source_message_id="msg-original",
            accepted=True,
            decision_id="decision-substituted",
        ))

    saved = store.list_proposals(accepted=True)[0]
    assert saved["source_message_id"] == "msg-original"
    assert saved["decision_id"] == "decision-original"


def test_reviewed_knowledge_provenance_and_evidence_cannot_be_silently_rewritten(tmp_path):
    store = ConversationKnowledgeStore(tmp_path / "knowledge.sqlite3")
    store.save_intent(UserIntent(
        intent_id="intent-provenance-guard", statement="Preserve source provenance",
        status="confirmed", source_conversation_id="conv-original", source_message_id="msg-original",
        evidence=["conv-original#msg-original"], confidence=1.0, reviewed_by_user=True,
    ))
    with pytest.raises(ValueError, match="Reviewed intent is immutable"):
        store.save_intent(UserIntent(
            intent_id="intent-provenance-guard", statement="Preserve source provenance",
            status="confirmed", source_conversation_id="conv-substituted", source_message_id="msg-substituted",
            evidence=["conv-substituted#msg-substituted"], confidence=1.0, reviewed_by_user=True,
        ))
    saved_intent = store.get_intent("intent-provenance-guard")
    assert saved_intent["source_message_id"] == "msg-original"
    assert saved_intent["evidence"] == ["conv-original#msg-original"]

    store.save_decision(UserDecision(
        decision_id="decision-provenance-guard", statement="Do not silently replace confirmed decisions",
        status="confirmed", source_conversation_id="conv-original", source_message_id="msg-original",
        evidence=["conv-original#msg-original"], confirmed_by_user=True,
    ))
    with pytest.raises(ValueError, match="User-confirmed decision is immutable"):
        store.save_decision(UserDecision(
            decision_id="decision-provenance-guard", statement="Do not silently replace confirmed decisions",
            status="confirmed", source_conversation_id="conv-original", source_message_id="msg-substituted",
            evidence=["conv-original#msg-substituted"], confirmed_by_user=True,
        ))
    saved_decision = store.get_decision("decision-provenance-guard")
    assert saved_decision["source_message_id"] == "msg-original"
    assert saved_decision["evidence"] == ["conv-original#msg-original"]

    store.save_relation(ConversationRelation(
        relation_id="relation-evidence-guard", source_conversation_id="conv-a", target_conversation_id="conv-b",
        relation_type="continues", evidence=["explicit continuation"], confidence=1.0, reviewed_by_user=True,
    ))
    with pytest.raises(ValueError, match="Reviewed relation is immutable"):
        store.save_relation(ConversationRelation(
            relation_id="relation-evidence-guard", source_conversation_id="conv-a", target_conversation_id="conv-b",
            relation_type="continues", evidence=["unsupported replacement evidence"], confidence=0.5,
            reviewed_by_user=True,
        ))
    saved_relation = store.list_relations("conv-a")[0]
    assert saved_relation["evidence"] == ["explicit continuation"]
    assert saved_relation["confidence"] == 1.0
