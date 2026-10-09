# Path: C:\ProgramasGodMode\DGM-MAT\core\organization\office.py
"""Canonical expanded office roster for DGM-MAT.

This module declares digital roles; it does not start autonomous workers.
Execution remains behind the governed delegation/runtime boundary.
"""
from __future__ import annotations

from .bootstrap import bootstrap_registry
from .models import AgentProfile, AgentStatus, Department
from .registry import AgentRegistry


OFFICE_DEPARTMENTS = (
    Department("backend-reliability", "Backend & Reliability", "API, service lifecycle, recovery, logging and operational stability", ["python", "fastapi", "reliability"], ["repo:read", "repo:write:backend", "tests:run"]),
    Department("frontend", "Frontend & Cockpit", "PC cockpit, mobile cockpit, accessibility and UI-client integration", ["frontend", "ui", "accessibility"], ["repo:read", "repo:write:frontend", "tests:run"]),
    Department("api-integration", "API & Integration", "Contracts, clients, schemas, compatibility and integration tests", ["api", "contracts", "integration"], ["repo:read", "repo:write:api", "tests:run"]),
    Department("repository-intelligence", "Repository Intelligence", "Repository inventory, project trees, ownership maps and drift detection", ["inventory", "tree", "architecture"], ["repo:read", "reports:write"]),
    Department("security", "Security Engineering", "Threat modelling, auth boundaries, route scopes and security regression tests", ["security", "auth", "threat-model"], ["repo:read", "repo:write:security", "tests:run"]),
    Department("memory-governance", "Memory & Documentation", "Persistent memory, decision records, project docs and provenance", ["memory", "documentation", "provenance"], ["repo:read", "docs:write", "memory:propose"]),
    Department("back-office", "Back Office Operations", "Task administration, evidence records, schedules and cross-project coordination", ["operations", "coordination", "records"], ["repo:read", "reports:write", "tasks:manage"]),
    Department("front-office", "Front Office & Product", "User intent, requirements clarification, acceptance criteria and cockpit workflows", ["requirements", "product", "acceptance"], ["repo:read", "tasks:propose"]),
    Department("browser-automation", "Browser Automation", "Operate only authorized browser sessions within legitimate free-tier terms", ["browser", "free-tier", "session-safety"], ["tasks:read", "reports:write"]),
    Department("cost-governance", "Cost & Quota Governance", "Enforce FREE-ONLY defaults, quota checks and paid-deny controls", ["cost-control", "quota", "policy"], ["repo:read", "tests:run", "reports:write"]),
    Department("self-improvement", "Self-Improvement Engineering", "Improve DGM-MAT through reversible changes, tests and independent review", ["self-improvement", "refactoring", "regression"], ["repo:read", "repo:write:sandbox", "tests:run"]),
    Department("local-runtime", "Local Runtime & Models", "Monitor local model capacity, memory, runtime health and resource limits", ["ollama", "runtime", "resource-monitoring"], ["repo:read", "tests:run", "reports:write"]),
)

OFFICE_AGENTS = (
    AgentProfile("agent:backend-reliability", "Backend Reliability Engineer", "backend-reliability", "backend-engineer", ["python", "fastapi", "windows-service", "logging", "recovery"], ["Maintain headless backend stability", "Protect lifecycle and API health"], ["repo:read", "repo:write:backend", "tests:run"], supervisor_id="agent:hq-orchestrator", memory_scope="project"),
    AgentProfile("agent:frontend-engineer", "Frontend & Cockpit Engineer", "frontend", "frontend-engineer", ["typescript", "react", "mobile-ui", "accessibility"], ["Implement PC/mobile client after backend contract stabilizes"], ["repo:read", "repo:write:frontend", "tests:run"], supervisor_id="agent:hq-orchestrator", memory_scope="project"),
    AgentProfile("agent:api-integrator", "API Contract Integrator", "api-integration", "api-integrator", ["openapi", "fastapi", "http", "websocket", "contract-tests"], ["Keep API schemas and client integrations compatible"], ["repo:read", "repo:write:api", "tests:run"], supervisor_id="agent:hq-orchestrator", memory_scope="project"),
    AgentProfile("agent:bug-hunter", "Independent Bug Hunter", "bug-hunters", "bug-hunter", ["reproduction", "static-analysis", "regression", "fault-isolation", "negative-tests"], ["Find defects independently", "Reproduce failures and report evidence before proposing fixes"], ["repo:read", "tests:run", "reports:write"], supervisor_id="agent:hq-orchestrator", memory_scope="project"),
    AgentProfile("agent:repository-cartographer", "Repository Cartographer", "repository-intelligence", "repository-inventory", ["file-inventory", "project-tree", "dependency-map", "drift-detection"], ["Generate reproducible trees and file inventories", "Detect stale, duplicate and untracked artifacts without deleting them"], ["repo:read", "reports:write"], supervisor_id="agent:hq-orchestrator", memory_scope="project"),
    AgentProfile("agent:security-engineer", "Security Engineer", "security", "security-review", ["auth", "authorization", "websocket-security", "threat-model"], ["Review security boundaries independently", "Block remote exposure until route enforcement is proven"], ["repo:read", "repo:write:security", "tests:run"], supervisor_id="agent:hq-orchestrator", memory_scope="project"),
    AgentProfile("agent:memory-steward", "Memory & Documentation Steward", "memory-governance", "memory-steward", ["markdown", "decision-records", "provenance", "andreos-memory"], ["Record verified state and next actions in persistent memory"], ["repo:read", "docs:write", "memory:propose"], supervisor_id="agent:hq-orchestrator", memory_scope="institutional"),
    AgentProfile("agent:back-office-coordinator", "Back Office Coordinator", "back-office", "operations-coordinator", ["task-lifecycle", "scheduling", "evidence", "cross-project"], ["Maintain task ownership, checkpoints and evidence records"], ["repo:read", "reports:write", "tasks:manage"], supervisor_id="agent:hq-orchestrator", memory_scope="institutional"),
    AgentProfile("agent:front-office-analyst", "Front Office Requirements Analyst", "front-office", "requirements-analyst", ["requirements", "acceptance-criteria", "user-intent", "workflow-analysis"], ["Translate user intent into testable requirements", "Flag ambiguity before risky changes"], ["repo:read", "tasks:propose"], supervisor_id="agent:hq-orchestrator", memory_scope="project"),
    AgentProfile("agent:free-browser-operator", "Free Browser Collaboration Operator", "browser-automation", "free-browser-collaborator", ["browser-sessions", "free-tier-policy", "handoff-packets", "session-safety"], ["Prepare and operate only authorized free-mode AI sessions when a compliant adapter is implemented", "Stop on quota limits and never upgrade or spend"], ["tasks:read", "reports:write"], status=AgentStatus.OFFLINE, supervisor_id="agent:hq-orchestrator", memory_scope="project", metadata={"execution_maturity": "ROLE_DEFINED_ONLY", "activation_blocker": "No verified compliant browser-session adapter is integrated."}),
    AgentProfile("agent:cost-guardian", "Cost and Quota Guardian", "cost-governance", "cost-guardian", ["zero-cost-policy", "quota-verification", "billing-safety", "negative-tests"], ["Block unknown, paid, or exhausted routes before invocation", "Audit provider and credit consumption boundaries"], ["repo:read", "tests:run", "reports:write"], status=AgentStatus.OFFLINE, supervisor_id="agent:hq-orchestrator", memory_scope="institutional", metadata={"execution_maturity": "ROLE_DEFINED_ONLY", "activation_blocker": "Must be connected to the governed execution gate and independently tested."}),
    AgentProfile("agent:self-improvement-engineer", "Self-Improvement Engineer", "self-improvement", "self-improvement", ["sandboxed-refactoring", "backup-sha256", "test-driven-changes", "independent-review"], ["Propose and test reversible DGM-MAT improvements", "Never bypass approvals or modify protected mirrors"], ["repo:read", "repo:write:sandbox", "tests:run"], status=AgentStatus.OFFLINE, supervisor_id="agent:hq-orchestrator", memory_scope="project", metadata={"execution_maturity": "ROLE_DEFINED_ONLY", "activation_blocker": "Controlled self-improvement execution pipeline is not yet integrated end-to-end."}),
    AgentProfile("agent:local-runtime-engineer", "Local Runtime and Model Engineer", "local-runtime", "local-runtime", ["ollama", "memory-pressure", "health-checks", "resource-aware-routing"], ["Prefer local resources when hardware health allows", "Prevent model selection that exceeds available memory"], ["repo:read", "tests:run", "reports:write"], status=AgentStatus.OFFLINE, supervisor_id="agent:hq-orchestrator", memory_scope="project", metadata={"execution_maturity": "ROLE_DEFINED_ONLY", "activation_blocker": "Needs a verified resource-aware execution adapter and runtime health signals."}),
)


def bootstrap_full_office(registry: AgentRegistry | None = None) -> AgentRegistry:
    """Create the pilot organization plus specialist departments and roles."""
    registry = registry or AgentRegistry()
    bootstrap_registry(registry)
    for department in OFFICE_DEPARTMENTS:
        if registry.get_department(department.department_id) is None:
            registry.register_department(department)
    for agent in OFFICE_AGENTS:
        if registry.get_agent(agent.agent_id) is None:
            registry.register_agent(agent)
    return registry
