from copy import deepcopy

from core.self_evolution.evolution_guardrails import EvolutionGuardrails
from core.self_evolution.promotion_engine import PromotionEngine


def test_policy_enforcement_fails_closed_until_evaluator_is_wired():
    guardrails = EvolutionGuardrails()

    seemingly_acceptable_proposal = {
        "module": "core/example.py",
        "confidence": 0.99,
        "risk_score": 1,
        "status": "approved",
    }

    assert guardrails.enforce_policy(seemingly_acceptable_proposal) is False
    assert guardrails.enforce_policy(None) is False


def test_promotion_refuses_to_claim_success_without_implementation():
    engine = PromotionEngine()
    patch = {
        "module": "core/example.py",
        "diff": "diff --git a/core/example.py b/core/example.py",
        "risk_score": 1,
    }
    before = deepcopy(patch)

    assert engine.promote(patch) is False
    assert patch == before


def test_promotion_rejects_invalid_candidate_without_exception():
    engine = PromotionEngine()

    assert engine.promote(None) is False
    assert engine.promote({}) is False
