# Path: C:\ProgramasGodMode\DGM-MAT\tests\organization\test_office_delegation.py
from core.organization.delegation import DelegationEngine, DelegationError
from core.organization.models import AgentStatus, Task, TaskStatus
from core.organization.office import bootstrap_full_office
from core.organization.registry import AgentRegistry
from core.organization.message_bus import InternalMessageBus
from core.organization.task_manager import OrganizationTaskManager
from core.organization.worker_runtime import WorkerRuntime


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


def test_company_roster_declares_zero_cost_browser_and_self_improvement_roles_as_offline_until_verified():
    registry = bootstrap_full_office(AgentRegistry())
    expected = {
        "agent:free-browser-operator": "browser-automation",
        "agent:cost-guardian": "cost-governance",
        "agent:self-improvement-engineer": "self-improvement",
        "agent:local-runtime-engineer": "local-runtime",
    }
    for agent_id, department_id in expected.items():
        agent = registry.get_agent(agent_id)
        assert agent is not None
        assert agent.department_id == department_id
        assert agent.status == AgentStatus.OFFLINE
        assert agent.metadata["execution_maturity"] == "ROLE_DEFINED_ONLY"
    assert registry.get_department("browser-automation") is not None
    assert registry.get_department("cost-governance") is not None
    assert registry.get_department("self-improvement") is not None
    assert registry.get_department("local-runtime") is not None


def test_delegation_selects_exact_skill_match_and_assigns_task():
    registry = bootstrap_full_office(AgentRegistry())
    tasks = OrganizationTaskManager()
    runtime = WorkerRuntime(InternalMessageBus())
    runtime.register_handler("agent:repository-cartographer", lambda message: {"status": "handled"})
    task = Task(
        "task:inventory", "Inventory repository", "mission:test", "Create tree",
        metadata={"required_skills": ["file-inventory", "project-tree"], "required_permissions": ["reports:write"]},
    )
    tasks.create(task)
    decision = DelegationEngine(registry, tasks, runtime).delegate(task.task_id)
    assert decision.agent_id == "agent:repository-cartographer"
    assert set(decision.matched_skills) == {"file-inventory", "project-tree"}
    assert tasks.get(task.task_id).status == TaskStatus.ASSIGNED


def test_delegation_refuses_unavailable_or_unauthorized_agent():
    registry = bootstrap_full_office(AgentRegistry())
    registry.set_status("agent:repository-cartographer", AgentStatus.OFFLINE)
    tasks = OrganizationTaskManager()
    runtime = WorkerRuntime(InternalMessageBus())
    runtime.register_handler("agent:repository-cartographer", lambda message: {"status": "handled"})
    task = Task(
        "task:restricted", "Restricted inventory", "mission:test", "No write",
        metadata={"required_skills": ["file-inventory"], "required_permissions": ["repo:write:production"]},
    )
    tasks.create(task)
    try:
        DelegationEngine(registry, tasks, runtime).delegate(task.task_id)
    except DelegationError as exc:
        assert "No available agent" in str(exc)
    else:
        raise AssertionError("Delegation must reject agents lacking required permission.")


def test_delegation_refuses_unsatisfied_dependencies():
    registry = bootstrap_full_office(AgentRegistry())
    tasks = OrganizationTaskManager()
    runtime = WorkerRuntime(InternalMessageBus())
    runtime.register_handler("agent:repository-cartographer", lambda message: {"status": "handled"})
    tasks.create(Task("task:dependency", "Dependency", "mission:test", "Pending"))
    tasks.create(Task("task:blocked", "Blocked", "mission:test", "Wait", dependencies=["task:dependency"]))
    try:
        DelegationEngine(registry, tasks, runtime).delegate("task:blocked")
    except DelegationError as exc:
        assert "unsatisfied dependencies" in str(exc)
    else:
        raise AssertionError("Dependencies must be enforced.")


def test_available_role_without_registered_handler_is_not_delegable():
    registry = bootstrap_full_office(AgentRegistry())
    tasks = OrganizationTaskManager()
    task = Task(
        "task:no-handler",
        "Inventory repository",
        "mission:test",
        "Create tree",
        metadata={"required_skills": ["file-inventory"], "required_permissions": ["reports:write"]},
    )
    tasks.create(task)
    runtime = WorkerRuntime(InternalMessageBus())

    try:
        DelegationEngine(registry, tasks, runtime).delegate(task.task_id)
    except DelegationError as exc:
        assert "registered handler" in str(exc)
    else:
        raise AssertionError("An AVAILABLE role without a registered handler must not receive work.")


def test_worker_runtime_exposes_registered_handler_inventory():
    runtime = WorkerRuntime(InternalMessageBus())
    assert runtime.has_handler("agent:repository-cartographer") is False
    runtime.register_handler("agent:repository-cartographer", lambda message: {"status": "handled"})
    assert runtime.has_handler("agent:repository-cartographer") is True
    assert runtime.registered_agents() == ("agent:repository-cartographer",)
