# Path: C:\ProgramasGodMode\DGM-MAT\tests\organization\test_office_delegation.py
from core.organization.delegation import DelegationEngine, DelegationError
from core.organization.models import AgentStatus, Task, TaskStatus
from core.organization.office import bootstrap_full_office
from core.organization.registry import AgentRegistry
from core.organization.task_manager import OrganizationTaskManager


def test_full_office_bootstrap_is_idempotent_and_includes_specialists():
    registry = bootstrap_full_office(AgentRegistry())
    before = registry.snapshot()
    assert bootstrap_full_office(registry) is registry
    assert registry.snapshot() == before
    for agent_id in (
        "agent:bug-hunter", "agent:repository-cartographer",
        "agent:frontend-engineer", "agent:back-office-coordinator",
        "agent:front-office-analyst", "agent:security-engineer",
    ):
        assert registry.get_agent(agent_id) is not None


def test_delegation_selects_exact_skill_match_and_assigns_task():
    registry = bootstrap_full_office(AgentRegistry())
    tasks = OrganizationTaskManager()
    task = Task(
        "task:inventory", "Inventory repository", "mission:test", "Create tree",
        metadata={"required_skills": ["file-inventory", "project-tree"], "required_permissions": ["reports:write"]},
    )
    tasks.create(task)
    decision = DelegationEngine(registry, tasks).delegate(task.task_id)
    assert decision.agent_id == "agent:repository-cartographer"
    assert set(decision.matched_skills) == {"file-inventory", "project-tree"}
    assert tasks.get(task.task_id).status == TaskStatus.ASSIGNED


def test_delegation_refuses_unavailable_or_unauthorized_agent():
    registry = bootstrap_full_office(AgentRegistry())
    registry.set_status("agent:repository-cartographer", AgentStatus.OFFLINE)
    tasks = OrganizationTaskManager()
    task = Task(
        "task:restricted", "Restricted inventory", "mission:test", "No write",
        metadata={"required_skills": ["file-inventory"], "required_permissions": ["repo:write:production"]},
    )
    tasks.create(task)
    try:
        DelegationEngine(registry, tasks).delegate(task.task_id)
    except DelegationError as exc:
        assert "No available agent" in str(exc)
    else:
        raise AssertionError("Delegation must reject agents lacking required permission.")


def test_delegation_refuses_unsatisfied_dependencies():
    registry = bootstrap_full_office(AgentRegistry())
    tasks = OrganizationTaskManager()
    tasks.create(Task("task:dependency", "Dependency", "mission:test", "Pending"))
    tasks.create(Task("task:blocked", "Blocked", "mission:test", "Wait", dependencies=["task:dependency"]))
    try:
        DelegationEngine(registry, tasks).delegate("task:blocked")
    except DelegationError as exc:
        assert "unsatisfied dependencies" in str(exc)
    else:
        raise AssertionError("Dependencies must be enforced.")
