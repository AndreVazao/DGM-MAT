"""Typed task dispatch to fixed, read-only repository worker operations."""
from __future__ import annotations

from typing import Any

from .delegation import DelegationEngine
from .read_only_worker_orchestrator import ReadOnlyWorkerOrchestrator
from .task_manager import OrganizationTaskManager
from .models import TaskStatus


class OrganizationTaskDispatcher:
    """Dispatch only explicit task kinds; never interpret free-form descriptions."""

    TASK_KINDS = {
        "repository_inventory": {
            "agent_id": "agent:repository-cartographer",
            "capabilities": ("file-inventory", "project-tree"),
        },
        "python_source_analysis": {
            "agent_id": "agent:python-source-analyst",
            "capabilities": (
                "python-source-analysis",
                "python-syntax",
                "python-import-analysis",
            ),
        },
        "python_test_inventory": {
            "agent_id": "agent:python-test-inventory",
            "capabilities": (
                "python-test-inventory",
                "python-test-structure",
                "python-test-gap-signals",
            ),
        },
    }

    def __init__(
        self,
        tasks: OrganizationTaskManager,
        delegation: DelegationEngine,
        orchestrator: ReadOnlyWorkerOrchestrator,
    ) -> None:
        self.tasks = tasks
        self.delegation = delegation
        self.orchestrator = orchestrator

    @staticmethod
    def _blocked(reason: str, task_id: str) -> dict[str, Any]:
        return {
            "status": "BLOCKED",
            "task_id": task_id,
            "reason": reason,
            "code_mutation": False,
        }

    def dispatch(self, task_id: str) -> dict[str, Any]:
        task = self.tasks.get(task_id)
        if task is None:
            raise KeyError(task_id)

        if task.status == TaskStatus.COMPLETED:
            execution = task.metadata.get("worker_execution", {})
            if isinstance(execution, dict) and execution.get("durable_receipt") is True:
                return {
                    "status": "ALREADY_COMPLETED",
                    "task_id": task_id,
                    "message_id": execution.get("message_id"),
                    "result": execution.get("result"),
                    "durable_receipt": True,
                    "task_status": task.status.value,
                }
            return self._blocked("completed_without_worker_receipt", task_id)

        if task.status != TaskStatus.ASSIGNED:
            return self._blocked("task_not_assigned", task_id)
        if not isinstance(task.metadata, dict):
            return self._blocked("task_metadata_invalid", task_id)

        task_kind = task.metadata.get("task_kind")
        worker = self.TASK_KINDS.get(task_kind) if isinstance(task_kind, str) else None
        if worker is None:
            return self._blocked("task_kind_not_allowed", task_id)

        agent_id = worker["agent_id"]
        if task.assigned_agent != agent_id:
            return self._blocked("assigned_agent_does_not_match_task_kind", task_id)

        candidates = {
            profile.agent_id
            for profile, _score, _matched in self.delegation.candidates(task)
        }
        if agent_id not in candidates:
            return self._blocked("assigned_agent_not_currently_eligible", task_id)
        if not self.delegation.worker_runtime.declares_capabilities(
            agent_id, worker["capabilities"]
        ):
            return self._blocked("worker_capabilities_not_registered", task_id)

        repository_id = task.metadata.get("repository_id")
        if not isinstance(repository_id, str) or not repository_id.strip():
            return self._blocked("repository_id_required", task_id)

        response = self.orchestrator.run(
            agent_id=agent_id,
            repository_id=repository_id,
            mission_id=task.mission_id,
            correlation_id=f"task:{task.task_id}",
            task_id=task.task_id,
        )
        if not isinstance(response, dict):
            return {
                "status": "RESULT_UNVERIFIED",
                "task_id": task_id,
                "task_status": task.status.value,
                "reason": "worker_response_invalid",
            }
        status = response.get("status")
        if status in {"COMPLETED", "ALREADY_COMPLETED"}:
            if (
                response.get("durable_receipt") is not True
                or not isinstance(response.get("message_id"), str)
                or not isinstance(response.get("result"), dict)
            ):
                return {
                    **response,
                    "status": "RESULT_UNVERIFIED",
                    "task_id": task_id,
                    "task_status": task.status.value,
                    "reason": "durable_worker_receipt_required",
                }
            completed = self.tasks.complete_with_result(
                task_id,
                result=response["result"],
                message_id=response["message_id"],
            )
            return {
                **response,
                "task_id": task_id,
                "task_status": completed.status.value,
            }

        return {
            **response,
            "task_id": task_id,
            "task_status": task.status.value,
        }
