from __future__ import annotations

import pytest

from core.organization.models import AgentProfile, AgentStatus, Department
from core.organization.office import bootstrap_full_office
from core.organization.registry import AgentRegistry


def test_office_bootstrap_merges_richer_duplicate_bug_hunter_profile():
    registry = bootstrap_full_office(AgentRegistry())
    bug_hunter = registry.get_agent("agent:bug-hunter")

    assert bug_hunter is not None
    assert bug_hunter.role == "bug-hunter"
    assert {
        "reproduction",
        "static-analysis",
        "regression",
        "fault-isolation",
        "negative-tests",
    }.issubset(set(bug_hunter.skills))
    assert "Find defects independently" in bug_hunter.responsibilities
    # Reconciliation never grants the OFFICE_AGENTS permission declaration.
    assert bug_hunter.permissions == []


def test_reconciliation_preserves_operator_status_permissions_and_metadata():
    registry = AgentRegistry()
    registry.register_department(Department("bug-hunters", "Bug Hunters", "Independent failure discovery"))
    registry.register_agent(
        AgentProfile(
            "agent:bug-hunter",
            "Operator Named Bug Hunter",
            "bug-hunters",
            "operator-custom-role",
            skills=["operator-skill"],
            permissions=["operator:explicit-scope"],
            status=AgentStatus.OFFLINE,
            metadata={
                "execution_maturity": "HANDLER_REGISTERED",
                "operator_note": "preserve this",
            },
        )
    )

    bootstrap_full_office(registry)
    bug_hunter = registry.get_agent("agent:bug-hunter")

    assert bug_hunter.status == AgentStatus.OFFLINE
    assert bug_hunter.permissions == ["operator:explicit-scope"]
    assert bug_hunter.metadata["execution_maturity"] == "HANDLER_REGISTERED"
    assert bug_hunter.metadata["operator_note"] == "preserve this"
    assert "operator-skill" in bug_hunter.skills
    assert "reproduction" in bug_hunter.skills
    assert bug_hunter.name == "Operator Named Bug Hunter"


def test_profile_reconciliation_is_idempotent_and_does_not_touch_updated_at():
    registry = bootstrap_full_office(AgentRegistry())
    before = registry.snapshot()
    updated_at = registry.get_agent("agent:bug-hunter").updated_at

    bootstrap_full_office(registry)

    assert registry.snapshot() == before
    assert registry.get_agent("agent:bug-hunter").updated_at == updated_at


def test_reconciliation_rejects_department_conflict():
    registry = AgentRegistry()
    registry.register_department(Department("engineering", "Engineering", "Build software"))
    registry.register_department(Department("security", "Security", "Review security"))
    registry.register_agent(AgentProfile("agent:worker", "Worker", "engineering", "engineer"))

    with pytest.raises(ValueError, match="Conflicting department"):
        registry.reconcile_agent_profile(
            AgentProfile("agent:worker", "Worker", "security", "security-reviewer")
        )


def test_reconciliation_registers_missing_agent_through_registry_validation():
    registry = AgentRegistry()
    registry.register_department(Department("research", "Research", "Evidence-based research"))
    declared = AgentProfile(
        "agent:research",
        "Research Specialist",
        "research",
        "researcher",
        skills=["technical-research"],
    )

    result = registry.reconcile_agent_profile(declared)

    assert result is declared
    assert registry.get_agent("agent:research") is declared
