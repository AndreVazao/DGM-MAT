"""Agent and department registry for the DGM-MAT organization."""

from __future__ import annotations

from dataclasses import asdict
from threading import RLock

from .models import AgentProfile, AgentStatus, Department


class AgentRegistry:
    """Thread-safe registry for digital employees and their departments.

    Persistence is intentionally kept outside this first foundation layer.
    The registry is the authoritative runtime view; a future persistence
    adapter can mirror it into the DGM-MAT event store / AndreOS memory.
    """

    def __init__(self) -> None:
        self._agents: dict[str, AgentProfile] = {}
        self._departments: dict[str, Department] = {}
        self._lock = RLock()

    def register_department(self, department: Department) -> None:
        with self._lock:
            self._departments[department.department_id] = department

    def register_agent(self, agent: AgentProfile) -> None:
        with self._lock:
            if agent.department_id not in self._departments:
                raise ValueError(
                    f"Unknown department for agent {agent.agent_id}: "
                    f"{agent.department_id}"
                )
            if agent.agent_id in self._agents:
                raise ValueError(f"Agent already registered: {agent.agent_id}")
            self._agents[agent.agent_id] = agent

    def get_agent(self, agent_id: str) -> AgentProfile | None:
        with self._lock:
            return self._agents.get(agent_id)

    def get_department(self, department_id: str) -> Department | None:
        with self._lock:
            return self._departments.get(department_id)

    def list_agents(
        self,
        *,
        department_id: str | None = None,
        status: AgentStatus | None = None,
    ) -> list[AgentProfile]:
        with self._lock:
            result = list(self._agents.values())
        if department_id is not None:
            result = [a for a in result if a.department_id == department_id]
        if status is not None:
            result = [a for a in result if a.status == status]
        return result

    def set_status(self, agent_id: str, status: AgentStatus) -> None:
        with self._lock:
            agent = self._agents[agent_id]
            agent.status = status

    def update_performance(self, agent_id: str, metric: str, value: float) -> None:
        if not 0.0 <= value <= 1.0:
            raise ValueError("Performance values must be between 0 and 1.")
        with self._lock:
            self._agents[agent_id].performance[metric] = value

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "departments": {
                    key: asdict(value) for key, value in self._departments.items()
                },
                "agents": {
                    key: asdict(value) for key, value in self._agents.items()
                },
            }
