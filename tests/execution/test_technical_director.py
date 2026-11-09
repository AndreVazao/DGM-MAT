from __future__ import annotations

import pytest

from core.execution.technical_director import (
    DirectorInputError,
    PeerReviewRound,
    QualityDecision,
    QualitySnapshot,
    ReviewNextAction,
    ReviewOutcome,
    TechnicalDirectorReviewPolicy,
    assess_code_change,
)


BASE = "a" * 40
CANDIDATE = "b" * 40


def snapshot(commit, *, checks=None, paths=(), covered=(), critical=0, high=0, diff=True, compile_ok=True):
    return QualitySnapshot(
        commit_sha=commit,
        checks=checks or {"unit": True, "integration": True},
        changed_paths=tuple(paths),
        covered_paths=tuple(covered),
        critical_findings=critical,
        high_findings=high,
        diff_check_passed=diff,
        compile_passed=compile_ok,
    )


def passing_assessment():
    return assess_code_change(
        snapshot(BASE),
        snapshot(CANDIDATE, paths=("core/example.py",), covered=("core/example.py",)),
        allowed_paths=("core", "tests"),
    )


def test_quality_gate_accepts_only_when_all_objective_gates_pass():
    result = passing_assessment()
    assert result.decision == QualityDecision.ACCEPT_FOR_PEER_REVIEW
    assert len(result.evidence_sha256) == 64
    assert "not proof of correctness" in result.reasons[-1]


def test_quality_gate_detects_regression_and_missing_checks():
    result = assess_code_change(
        snapshot(BASE),
        snapshot(CANDIDATE, checks={"unit": False}, paths=("core/example.py",), covered=("core/example.py",)),
        allowed_paths=("core",),
    )
    assert result.decision == QualityDecision.NEEDS_FIXES
    assert result.regressions == ("unit",)
    assert "missing:integration" in result.failed_checks


def test_quality_gate_blocks_out_of_scope_and_critical_security_increase():
    result = assess_code_change(
        snapshot(BASE),
        snapshot(CANDIDATE, paths=("secrets/key.txt",), covered=("secrets/key.txt",), critical=1),
        allowed_paths=("core",),
    )
    assert result.decision == QualityDecision.BLOCKED
    assert "secrets/key.txt" in result.reasons or "changed_paths_outside_declared_scope" in result.reasons


def test_quality_gate_requires_test_evidence_for_changed_paths():
    result = assess_code_change(
        snapshot(BASE),
        snapshot(CANDIDATE, paths=("core/example.py",)),
        allowed_paths=("core",),
    )
    assert result.decision == QualityDecision.NEEDS_FIXES
    assert result.uncovered_paths == ("core/example.py",)


def test_quality_gate_rejects_malformed_revisions():
    with pytest.raises(DirectorInputError):
        assess_code_change(snapshot("main"), snapshot(CANDIDATE), allowed_paths=("core",))


def test_peer_review_asks_second_provider_after_first_unresolved():
    quality = passing_assessment()
    policy = TechnicalDirectorReviewPolicy()
    result = policy.decide(
        author="codex",
        reviewers=("claude_code",),
        rounds=(PeerReviewRound(1, "codex", "claude_code", ReviewOutcome.UNRESOLVED, notes="Need evidence"),),
        quality=quality,
    )
    assert result.next_action == ReviewNextAction.WEB_RESEARCH_REQUIRED
    assert result.research_question


def test_peer_review_approves_only_after_independent_reviewer_and_quality_gate():
    quality = passing_assessment()
    policy = TechnicalDirectorReviewPolicy()
    result = policy.decide(
        author="codex",
        reviewers=("claude_code",),
        rounds=(PeerReviewRound(1, "codex", "claude_code", ReviewOutcome.APPROVE, notes="Reviewed diff and tests"),),
        quality=quality,
    )
    assert result.next_action == ReviewNextAction.ACCEPT_FOR_OPERATOR_APPROVAL


def test_peer_review_change_request_returns_to_author():
    result = TechnicalDirectorReviewPolicy().decide(
        author="claude_code",
        reviewers=("codex",),
        rounds=(PeerReviewRound(1, "claude_code", "codex", ReviewOutcome.REQUEST_CHANGES, ("missing regression test",)),),
        quality=passing_assessment(),
    )
    assert result.next_action == ReviewNextAction.RETURN_TO_AUTHOR
    assert result.next_reviewer == "claude_code"


def test_peer_review_never_runs_when_objective_gate_fails():
    bad = assess_code_change(
        snapshot(BASE),
        snapshot(CANDIDATE, checks={"unit": False}, paths=("core/a.py",), covered=("core/a.py",)),
        allowed_paths=("core",),
    )
    result = TechnicalDirectorReviewPolicy().decide(
        author="codex", reviewers=("claude_code",), rounds=(), quality=bad,
    )
    assert result.next_action == ReviewNextAction.BLOCKED


def test_peer_review_rejects_self_review_and_non_contiguous_rounds():
    policy = TechnicalDirectorReviewPolicy()
    with pytest.raises(DirectorInputError):
        policy.decide(author="codex", reviewers=("codex",), rounds=(), quality=passing_assessment())
    with pytest.raises(DirectorInputError):
        policy.decide(
            author="codex", reviewers=("claude_code",),
            rounds=(PeerReviewRound(2, "codex", "claude_code", ReviewOutcome.UNRESOLVED),),
            quality=passing_assessment(),
        )


def test_research_escalation_does_not_grant_approval():
    result = TechnicalDirectorReviewPolicy().decide(
        author="codex",
        reviewers=("claude_code",),
        rounds=(PeerReviewRound(1, "codex", "claude_code", ReviewOutcome.UNRESOLVED),),
        quality=passing_assessment(),
        research_question="Does the upstream API support this flag?",
    )
    assert result.next_action == ReviewNextAction.WEB_RESEARCH_REQUIRED
    assert "upstream API" in result.research_question
