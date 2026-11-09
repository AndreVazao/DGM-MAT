"""Evidence-led technical director: objective quality gate and sequential peer review.

This module is a deterministic policy/state-machine layer. Provider calls,
web searches, code execution, approval, merge and deployment are deliberately
owned by separate host adapters and are not performed here.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Mapping


_FULL_SHA = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
_SAFE_PATH = re.compile(r"^[^\\\\]+$")


class DirectorInputError(ValueError):
    """Invalid or incomplete evidence supplied to the technical director."""


class QualityDecision(str, Enum):
    ACCEPT_FOR_PEER_REVIEW = "ACCEPT_FOR_PEER_REVIEW"
    NEEDS_FIXES = "NEEDS_FIXES"
    BLOCKED = "BLOCKED"


class ReviewOutcome(str, Enum):
    APPROVE = "APPROVE"
    REQUEST_CHANGES = "REQUEST_CHANGES"
    UNRESOLVED = "UNRESOLVED"


class ReviewNextAction(str, Enum):
    ACCEPT_FOR_OPERATOR_APPROVAL = "ACCEPT_FOR_OPERATOR_APPROVAL"
    RETURN_TO_AUTHOR = "RETURN_TO_AUTHOR"
    ASK_NEXT_INDEPENDENT_REVIEWER = "ASK_NEXT_INDEPENDENT_REVIEWER"
    REVIEW_REVISED_RESULT = "REVIEW_REVISED_RESULT"
    WEB_RESEARCH_REQUIRED = "WEB_RESEARCH_REQUIRED"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class QualitySnapshot:
    """Machine-verifiable evidence for one immutable Git revision."""

    commit_sha: str
    checks: Mapping[str, bool]
    changed_paths: tuple[str, ...] = ()
    covered_paths: tuple[str, ...] = ()
    critical_findings: int = 0
    high_findings: int = 0
    diff_check_passed: bool = False
    compile_passed: bool = False


@dataclass(frozen=True, slots=True)
class QualityAssessment:
    decision: QualityDecision
    baseline_sha: str
    candidate_sha: str
    regressions: tuple[str, ...]
    failed_checks: tuple[str, ...]
    uncovered_paths: tuple[str, ...]
    security_delta: Mapping[str, int]
    evidence_sha256: str
    reasons: tuple[str, ...]

    def to_dict(self) -> dict:
        result = asdict(self)
        result["decision"] = self.decision.value
        return result


def assess_code_change(
    baseline: QualitySnapshot,
    candidate: QualitySnapshot,
    *,
    allowed_paths: tuple[str, ...],
) -> QualityAssessment:
    """Compare before/after evidence; never infer quality from prose or model confidence."""
    for label, snapshot in (("baseline", baseline), ("candidate", candidate)):
        if not isinstance(snapshot, QualitySnapshot):
            raise DirectorInputError(f"{label}_snapshot_required")
        if not isinstance(snapshot.commit_sha, str) or not _FULL_SHA.fullmatch(snapshot.commit_sha):
            raise DirectorInputError(f"{label}_commit_must_be_full_sha")
        if not isinstance(snapshot.checks, Mapping) or not snapshot.checks:
            raise DirectorInputError(f"{label}_checks_required")
        if any(not isinstance(k, str) or not k.strip() or type(v) is not bool for k, v in snapshot.checks.items()):
            raise DirectorInputError(f"{label}_checks_must_be_named_booleans")
        if any(type(value) is not int or value < 0 for value in (snapshot.critical_findings, snapshot.high_findings)):
            raise DirectorInputError(f"{label}_security_counts_invalid")
        for path in snapshot.changed_paths + snapshot.covered_paths:
            if not isinstance(path, str) or not path or path.startswith("/") or ".." in path.split("/") or "\\" in path:
                raise DirectorInputError(f"{label}_path_invalid")

    if baseline.commit_sha == candidate.commit_sha:
        raise DirectorInputError("baseline_and_candidate_must_differ")
    if not allowed_paths or any(not isinstance(p, str) or not p or p.startswith("/") or ".." in p.split("/") or "\\" in p for p in allowed_paths):
        raise DirectorInputError("safe_allowed_paths_required")

    baseline_names = set(baseline.checks)
    candidate_names = set(candidate.checks)
    missing_checks = sorted(baseline_names - candidate_names)
    regressions = sorted(name for name in baseline_names & candidate_names if baseline.checks[name] and not candidate.checks[name])
    failed_checks = sorted(name for name, passed in candidate.checks.items() if not passed)
    failed_checks.extend(f"missing:{name}" for name in missing_checks)

    allowed = tuple(allowed_paths)
    out_of_scope = sorted(
        path for path in candidate.changed_paths
        if not any(path == prefix or path.startswith(prefix.rstrip("/") + "/") for prefix in allowed)
    )
    uncovered = sorted(set(candidate.changed_paths) - set(candidate.covered_paths))
    security_delta = {
        "critical": candidate.critical_findings - baseline.critical_findings,
        "high": candidate.high_findings - baseline.high_findings,
    }
    reasons: list[str] = []
    if regressions:
        reasons.append("previously_passing_checks_regressed")
    if failed_checks:
        reasons.append("candidate_checks_failed_or_missing")
    if not candidate.diff_check_passed:
        reasons.append("git_diff_check_failed")
    if not candidate.compile_passed:
        reasons.append("compile_check_failed")
    if security_delta["critical"] > 0 or security_delta["high"] > 0:
        reasons.append("security_findings_increased")
    if uncovered:
        reasons.append("changed_paths_without_test_evidence")
    if out_of_scope:
        reasons.append("changed_paths_outside_declared_scope")

    if out_of_scope or security_delta["critical"] > 0:
        decision = QualityDecision.BLOCKED
    elif reasons:
        decision = QualityDecision.NEEDS_FIXES
    else:
        decision = QualityDecision.ACCEPT_FOR_PEER_REVIEW
        reasons.append("no_measured_regressions_and_all_declared_gates_passed; this is not proof of correctness")

    payload = {
        "baseline": asdict(baseline),
        "candidate": asdict(candidate),
        "allowed_paths": list(allowed_paths),
        "regressions": regressions,
        "failed_checks": sorted(set(failed_checks)),
        "uncovered_paths": uncovered,
        "out_of_scope": out_of_scope,
        "security_delta": security_delta,
        "reasons": reasons,
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return QualityAssessment(
        decision=decision,
        baseline_sha=baseline.commit_sha,
        candidate_sha=candidate.commit_sha,
        regressions=tuple(regressions),
        failed_checks=tuple(sorted(set(failed_checks))),
        uncovered_paths=tuple(uncovered),
        security_delta=security_delta,
        evidence_sha256=digest,
        reasons=tuple(reasons),
    )


@dataclass(frozen=True, slots=True)
class PeerReviewRound:
    round_number: int
    author: str
    reviewer: str
    outcome: ReviewOutcome
    blocking_findings: tuple[str, ...] = ()
    notes: str = ""


@dataclass(frozen=True, slots=True)
class PeerReviewDecision:
    next_action: ReviewNextAction
    next_reviewer: str | None
    rounds_used: int
    research_question: str | None
    reason: str


class TechnicalDirectorReviewPolicy:
    """Bounded, one-reviewer-at-a-time peer review with web research escalation."""

    ALLOWED_PROVIDERS = frozenset({"codex", "claude_code"})

    def __init__(self, *, max_rounds: int = 4) -> None:
        if isinstance(max_rounds, bool) or not isinstance(max_rounds, int) or not 1 <= max_rounds <= 6:
            raise DirectorInputError("max_rounds_must_be_between_1_and_6")
        self.max_rounds = max_rounds

    def decide(
        self,
        *,
        author: str,
        reviewers: tuple[str, ...],
        rounds: tuple[PeerReviewRound, ...],
        quality: QualityAssessment,
        research_question: str = "",
        author_revision_ready: bool = False,
    ) -> PeerReviewDecision:
        if author not in self.ALLOWED_PROVIDERS:
            raise DirectorInputError("author_provider_not_allowed")
        if not reviewers or any(r not in self.ALLOWED_PROVIDERS for r in reviewers):
            raise DirectorInputError("reviewers_must_be_codex_or_claude_code")
        if len(set(reviewers)) != len(reviewers) or author in reviewers:
            raise DirectorInputError("reviewers_must_be_unique_and_independent_from_author")
        if not isinstance(quality, QualityAssessment):
            raise DirectorInputError("quality_assessment_required")
        if quality.decision != QualityDecision.ACCEPT_FOR_PEER_REVIEW:
            return PeerReviewDecision(ReviewNextAction.BLOCKED, None, len(rounds), None, "objective_quality_gate_not_passed")
        if len(rounds) > self.max_rounds:
            return PeerReviewDecision(ReviewNextAction.BLOCKED, None, len(rounds), None, "review_round_budget_exceeded")

        for index, review in enumerate(rounds, start=1):
            if review.round_number != index:
                raise DirectorInputError("review_rounds_must_be_contiguous")
            if review.author != author or review.reviewer not in reviewers or review.reviewer == author:
                raise DirectorInputError("review_round_identity_mismatch")
            if not isinstance(review.outcome, ReviewOutcome):
                raise DirectorInputError("review_outcome_invalid")
            if not isinstance(review.notes, str) or len(review.notes) > 8000:
                raise DirectorInputError("review_notes_invalid")

        if rounds:
            latest = rounds[-1]
            if latest.outcome == ReviewOutcome.APPROVE and not latest.blocking_findings:
                return PeerReviewDecision(
                    ReviewNextAction.ACCEPT_FOR_OPERATOR_APPROVAL, None, len(rounds), None,
                    "objective_gates_passed_and_independent_peer_approved; operator approval still required",
                )
            if latest.outcome == ReviewOutcome.REQUEST_CHANGES and not author_revision_ready:
                return PeerReviewDecision(
                    ReviewNextAction.RETURN_TO_AUTHOR, author, len(rounds), None,
                    "peer_review_requested_changes; revise against cited findings before another review",
                )
            if latest.outcome == ReviewOutcome.REQUEST_CHANGES and author_revision_ready:
                return PeerReviewDecision(
                    ReviewNextAction.REVIEW_REVISED_RESULT, latest.reviewer, len(rounds), None,
                    "author_revision_ready; the same independent reviewer must verify the exact revised candidate",
                )

        used = {item.reviewer for item in rounds}
        available = [item for item in reviewers if item not in used]
        if available and len(rounds) < self.max_rounds:
            return PeerReviewDecision(
                ReviewNextAction.ASK_NEXT_INDEPENDENT_REVIEWER, available[0], len(rounds), None,
                "unresolved_or_blocking_review_requires_the_next_independent_reviewer",
            )

        question = research_question.strip() if isinstance(research_question, str) else ""
        if not question:
            question = "Resolve the remaining disputed code-review findings using current official documentation and reproducible evidence."
        return PeerReviewDecision(
            ReviewNextAction.WEB_RESEARCH_REQUIRED, None, len(rounds), question[:2000],
            "local_peer_reviewers_exhausted_or_disagreement_persists; research is evidence gathering, not approval",
        )
