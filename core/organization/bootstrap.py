"""Bootstrap the initial DGM-MAT digital organization without executing workers."""

from __future__ import annotations

from .models import AgentProfile, Department
from .registry import AgentRegistry


DEPARTMENTS = (
    Department("hq", "DGM-MAT HQ", "orchestration, governance and integration"),
    Department("engineering", "Engineering", "software architecture and implementation"),
    Department("qa", "Quality Assurance", "independent verification"),
    Department("bug-hunters", "Bug Hunters", "independent failure discovery"),
    Department("devops", "DevOps", "build, CI/CD and deployment"),
    Department("research", "Research", "evidence-based technical research"),
    Department("conversation-intelligence", "Conversation Intelligence", "conversation recovery and context"),
    Department("ai-liaison", "AI Provider Liaison", "provider-specific interaction"),
    Department("capability-acquisition", "Capability Acquisition & Skill Forge", "discover, adapt and promote capabilities"),
)

PILOT_AGENTS = (
    AgentProfile("agent:hq-orchestrator", "HQ Orchestrator", "hq", "orchestrator"),
    AgentProfile("agent:python-engineer", "Python Engineer", "engineering", "python"),
    AgentProfile("agent:qa", "QA", "qa", "quality"),
    AgentProfile("agent:bug-hunter", "Bug Hunter", "bug-hunters", "diagnostics"),
    AgentProfile("agent:conversation-intelligence", "Conversation Intelligence", "conversation-intelligence", "conversation-recovery"),
    AgentProfile("agent:devops", "DevOps", "devops", "deployment"),
    AgentProfile("agent:capability-scout", "Capability Scout", "capability-acquisition", "capability-discovery"),
)


def bootstrap_registry(registry: AgentRegistry) -> AgentRegistry:
    """Seed departments/workers exactly once; never deletes existing records."""
    for department in DEPARTMENTS:
        if registry.get_department(department.department_id) is None:
            registry.register_department(department)
    for agent in PILOT_AGENTS:
        if registry.get_agent(agent.agent_id) is None:
            registry.register_agent(agent)
    return registry
