"""Bridge exact natural-language mission intents to durable typed read-only workers.

This adapter never interprets a task description as a command. It accepts only
three fixed task kinds and a repository identifier that is resolved by the
host-owned worker allowlist.
"""
from __future__ import annotations

from uuid import uuid4
from typing import Any

from core.organization.models import Task, TaskStatus


class TypedOrganizationMissionExecutor:
    """Execute one registered read-only organization task for a mission."""

    INTENT_TO_KIND = {
        "organization_repository_inventory": "repository_inventory",
        "organization_python_source_analysis": "python_source_analysis",
        "organization_python_test_inventory": "python_test_inventory",
    }

    def __init__(self, tasks, delegation, dispatcher) -> None:
        self.tasks = tasks
        self.delegation = delegation
        self.dispatcher = dispatcher

    def execute(self, mission, intent: str) -> dict[str, Any]:
        task_kind = self.INTENT_TO_KIND.get(intent)
        if task_kind is None:
            raise ValueError("No typed organization executor is registered for this intent.")

        repository_id = self._repository_id(mission.goal)
        task_policy = self.dispatcher.TASK_KINDS.get(task_kind)
        if task_policy is None:
            raise RuntimeError("The typed task kind is not registered by the dispatcher.")

        task_id = f"mission_task_{uuid4().hex}"
        required_skills = list(task_policy["capabilities"])
        task = Task(
            task_id=task_id,
            title=f"{task_kind}: {repository_id}",
            mission_id=mission.mission_id,
            description=f"Run the fixed read-only operation {task_kind} on allowlisted repository {repository_id}.",
            priority=50,
            approval_required=False,
            metadata={
                "task_kind": task_kind,
                "repository_id": repository_id,
                "required_skills": required_skills,
                "code_mutation": False,
            },
        )
        self.tasks.create(task)

        decision = self.delegation.delegate(task_id)
        response = self.dispatcher.dispatch(task_id)
        if not isinstance(response, dict):
            raise RuntimeError("Typed worker returned an invalid response envelope.")

        if (
            response.get("status") not in {"COMPLETED", "ALREADY_COMPLETED"}
            or response.get("durable_receipt") is not True
            or not isinstance(response.get("message_id"), str)
            or not response.get("message_id").strip()
            or not isinstance(response.get("result"), dict)
        ):
            reason = response.get("reason") or response.get("status") or "worker_result_unverified"
            raise RuntimeError(f"Typed read-only worker did not produce a verified result: {reason}")

        persisted = self.tasks.get(task_id)
        if persisted is None or persisted.status != TaskStatus.COMPLETED:
            raise RuntimeError("Typed worker result was not durably finalized in the task store.")
        receipt = persisted.metadata.get("worker_execution", {})
        if (
            not isinstance(receipt, dict)
            or receipt.get("durable_receipt") is not True
            or receipt.get("message_id") != response["message_id"]
            or receipt.get("result") != response["result"]
        ):
            raise RuntimeError("Typed worker durable receipt does not match the returned result.")

        return {
            "handler": intent,
            "task_kind": task_kind,
            "task_id": task_id,
            "repository_id": repository_id,
            "agent_id": decision.agent_id,
            "message_id": response["message_id"],
            "durable_receipt": True,
            "read_only": True,
            "code_mutation": False,
            "result": response["result"],
        }

    @staticmethod
    def _repository_id(goal: str) -> str:
        import re
        import unicodedata

        normalized = unicodedata.normalize("NFKD", goal)
        normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
        normalized = " ".join(normalized.split())
        match = re.search(
            r"(?:repository|repositorio) ([a-z0-9][a-z0-9._-]{0,63})$",
            normalized,
            flags=re.IGNORECASE,
        )
        if match is None:
            raise ValueError(
                "Typed specialist missions must end with an explicit allowlist repository ID."
            )
        return match.group(1)
