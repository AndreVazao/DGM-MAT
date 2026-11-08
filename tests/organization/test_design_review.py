"""Contract tests for the read-only Elephant-Goldfish review packet builder."""
import pytest

from core.organization.design_review import (
    DesignBrief,
    ReviewFinding,
    ReviewerResult,
    build_reviewer_packets,
    result_to_dict,
    validate_independent_results,
)


def brief():
    return DesignBrief(
        title="Add searchable local conversation archive",
        problem="Conversation records are not consistently discoverable.",
        intended_outcome="Provide provenance-preserving local search.",
        constraints=("Local-first", "No paid provider dependency"),
        acceptance_criteria=("Search returns source identifiers",),
        source_evidence=("docs/architecture/archive.md#L10-L24",),
        task_id="task:design-review",
        mission_id="mission:archive",
    )


def test_packet_builder_creates_bounded_reviewer_specific_inputs():
    packets = build_reviewer_packets(
        brief(), ("reviewer:security", "reviewer:architecture"), "review:001"
    )

    assert len(packets) == 2
    assert packets[0].review_id == packets[1].review_id == "review:001"
    assert packets[0].reviewer_id != packets[1].reviewer_id
    assert packets[0].brief == packets[1].brief
    assert packets[0].context_policy == "FRESH_CONTEXT_REQUIRED"
    assert "author_conversation" in packets[0].forbidden_context
    assert "credentials" in packets[0].forbidden_context
    assert not hasattr(packets[0], "author_conversation")
    assert not hasattr(packets[0], "author_recommendation")


@pytest.mark.parametrize(
    "reviewer_ids",
    [
        ("reviewer:one",),
        ("reviewer:one", "reviewer:one"),
        tuple(f"reviewer:{index}" for index in range(6)),
    ],
)
def test_packet_builder_rejects_non_independent_reviewer_sets(reviewer_ids):
    with pytest.raises(ValueError):
        build_reviewer_packets(brief(), reviewer_ids, "review:bad")


def test_independence_requires_distinct_runtime_context_ids():
    packets = build_reviewer_packets(
        brief(), ("reviewer:security", "reviewer:architecture"), "review:002"
    )
    results = (
        ReviewerResult("review:002", "reviewer:security", "ctx:security"),
        ReviewerResult("review:002", "reviewer:architecture", "ctx:architecture"),
    )

    status = validate_independent_results(packets, results)

    assert status["independent"] is True
    assert status["distinct_runtime_contexts"] == 2
    assert status["runtime_isolation_attestation_required"] is True


def test_shared_runtime_context_never_counts_as_independent():
    packets = build_reviewer_packets(
        brief(), ("reviewer:security", "reviewer:architecture"), "review:003"
    )
    results = (
        ReviewerResult("review:003", "reviewer:security", "ctx:shared"),
        ReviewerResult("review:003", "reviewer:architecture", "ctx:shared"),
    )

    assert validate_independent_results(packets, results) == {
        "independent": False,
        "reason": "shared_runtime_context",
    }


def test_review_result_must_match_expected_reviewer_identity():
    packets = build_reviewer_packets(
        brief(), ("reviewer:security", "reviewer:architecture"), "review:004"
    )
    results = (
        ReviewerResult("review:004", "reviewer:security", "ctx:1"),
        ReviewerResult("review:004", "reviewer:other", "ctx:2"),
    )

    assert validate_independent_results(packets, results)["reason"] == (
        "reviewer_identity_mismatch"
    )


def test_findings_are_evidence_bounded_and_json_ready():
    finding = ReviewFinding(
        title="Archive source provenance is underspecified",
        severity="high",
        evidence="The design brief does not define stable source IDs.",
        impact="Imported records could become ambiguous after re-import.",
        recommendation="Specify provider and source ID uniqueness constraints.",
        confidence=0.9,
    )
    result = ReviewerResult(
        "review:005",
        "reviewer:data",
        "ctx:data",
        findings=(finding,),
    )

    payload = result_to_dict(result)

    assert payload["findings"][0]["severity"] == "high"
    assert payload["findings"][0]["confidence"] == 0.9
    with pytest.raises(ValueError):
        ReviewFinding("bad", "urgent", "evidence", "impact", "fix")
    with pytest.raises(ValueError):
        ReviewFinding("bad", "high", "evidence", "impact", "fix", 1.5)
