# Path: C:\ProgramasGodMode\DGM-MAT\core\organization\delegation.py
"""Deterministic, policy-bounded task delegation for the DGM-MAT office."""
from __future__ import annotations

from dataclasses import dataclass

from .models import AgentProfile, AgentStatus, Task, TaskStatus
from .registry import AgentRegistry
from .task_manager import OrganizationTaskManager


@dataclass(frozen=True, slots=True)
class DelegationDecision:
    task_id: str
    agent_id: str
    score: float
    matched_skills: tuple[str, ...]
    reason: str


class DelegationError(RuntimeError):
    """Raised when a task cannot be safely assigned to a registered worker."""


class DelegationEngine:
    """Assign tasks only to available agents satisfying explicit constraints.

    Task.metadata may define required_skills, required_permissions and
    preferred_department. This router assigns work but never executes it.
    """

    def __init__(self, registry: AgentRegistry, tasks: OrganizationTaskManager) -> None:
        self.registry = registry
        self.tasks = tasks

    @staticmethod
    def _strings(value: object) -> set[str]:
        if not isinstance(value, (list, tuple, set)):
            return set()
        return {item.strip().casefold() for item in value if isinstance(item, str) and item.strip()}

    def candidates(self, task: Task) -> list[tuple[AgentProfile, float, tuple[str, ...]]]:
        metadata = task.metadata or {}
        required_skills = self._strings(metadata.get("required_skills"))
        required_permissions = self._strings(metadata.get("required_permissions"))
        preferred_department = metadata.get("preferred_department")
        if preferred_department is not None and not isinstance(preferred_department, str):
            raise DelegationError("preferred_department must be a string.")

        result = []
        for agent in self.registry.list_agents(status=AgentStatus.AVAILABLE):
            department = self.registry.get_department(agent.department_id)
            if department is None or not department.active:
                continue
            if task.owner_department and agent.department_id != task.owner_department:
                continue
            if preferred_department and agent.department_id != preferred_department:
                continue
            skills = self._strings(agent.skills)
            capabilities = self._strings(department.capabilities)
            matched = required_skills.intersection(skills | capabilities)
            if not required_skills.issubset(skills | capabilities):
                continue
            if not required_permissions.issubset(self._strings(agent.permissions)):
                continue
            metrics = [value for value in agent.performance.values() if isinstance(value, (int, float))]
            reliability = sum(metrics) / len(metrics) if metrics else 0.5
            result.append((agent, len(matched) * 10.0 + reliability, tuple(sorted(matched))))
        result.sort(key=lambda item: (-item[1], item[0].agent_id))
        return result

    def delegate(self, task_id: str) -> DelegationDecision:
        task = self.tasks.get(task_id)
        if task is None:
            raise DelegationError(f"Unknown task: {task_id}")
        if task.status not in {TaskStatus.CREATED, TaskStatus.QUEUED}:
            raise DelegationError(f"Task {task_id} is not assignable from {task.status.value}.")
        if not self.tasks.dependencies_satisfied(task_id):
            raise DelegationError(f"Task {task_id} has unsatisfied dependencies.")
        candidates = self.candidates(task)
        if not candidates:
            raise DelegationError(f"No available agent satisfies task {task_id} constraints.")
        agent, score, matched = candidates[0]
        self.tasks.assign(task_id, agent.agent_id)
        return DelegationDecision(
            task_id=task_id,
            agent_id=agent.agent_id,
            score=score,
            matched_skills=matched,
            reason="Best available registered agent matching skills, department, dependencies and permissions.",
        )
