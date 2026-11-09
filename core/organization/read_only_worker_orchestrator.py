"""Mission-scoped dispatch for the explicitly registered read-only specialists."""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3

from .message_bus import InternalMessageBus
from .models import Message, MessagePriority
from .worker_runtime import WorkerRuntime


class ReadOnlyWorkerOrchestrator:
    """Send bounded typed requests and return durable worker receipts."""

    _REPOSITORY_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
    _WORKERS = {
        "agent:repository-cartographer": {
            "operation": "inventory_repository",
            "subject": "Read-only repository inventory",
            "capabilities": ("file-inventory", "project-tree"),
        },
        "agent:python-source-analyst": {
            "operation": "analyze_python_repository",
            "subject": "Read-only Python source analysis",
            "capabilities": ("python-source-analysis", "python-syntax", "python-import-analysis"),
        },
        "agent:python-test-inventory": {
            "operation": "inventory_python_tests",
            "subject": "Read-only Python test inventory",
            "capabilities": ("python-test-inventory", "python-test-structure", "python-test-gap-signals"),
        },
    }

    def __init__(self, bus: InternalMessageBus, runtime: WorkerRuntime) -> None:
        self.bus = bus
        self.runtime = runtime

    @staticmethod
    def _invalid(reason: str) -> dict:
        return {"status": "BLOCKED", "reason": reason, "code_executed": False}

    def run(
        self,
        *,
        agent_id: str,
        repository_id: str,
        mission_id: str,
        correlation_id: str,
        task_id: str | None = None,
    ) -> dict:
        worker = self._WORKERS.get(agent_id)
        if worker is None:
            return self._invalid("worker_not_allowed")
        if not isinstance(repository_id, str) or not self._REPOSITORY_ID.fullmatch(repository_id):
            return self._invalid("repository_id_invalid")
        for value, field in ((mission_id, "mission_id"), (correlation_id, "correlation_id")):
            if not isinstance(value, str) or not value.strip() or len(value) > 160:
                return self._invalid(f"{field}_invalid")
        if task_id is not None and (
            not isinstance(task_id, str) or not task_id.strip() or len(task_id) > 160
        ):
            return self._invalid("task_id_invalid")
        if not self.runtime.has_handler(agent_id):
            return self._invalid("worker_handler_not_registered")
        if not self.runtime.declares_capabilities(agent_id, worker["capabilities"]):
            return self._invalid("worker_capabilities_not_declared")

        body = json.dumps(
            {
                "schema_version": 1,
                "operation": worker["operation"],
                "repository_id": repository_id,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        identity = "\0".join((agent_id, repository_id, mission_id, correlation_id, body))
        message_id = "msg:readonly:" + hashlib.sha256(identity.encode("utf-8")).hexdigest()
        message = Message(
            sender_id="agent:hq-orchestrator",
            recipient_id=agent_id,
            subject=worker["subject"],
            body=body,
            message_id=message_id,
            task_id=task_id,
            mission_id=mission_id,
            priority=MessagePriority.NORMAL,
            requires_response=True,
            correlation_id=correlation_id,
        )
        try:
            self.bus.send(message)
        except (sqlite3.Error, OSError, ValueError, TypeError):
            return self._invalid("message_enqueue_failed")

        receipt = self.bus.get_dispatch_result(message_id)
        if receipt is not None:
            stored_result = receipt["result"]
            return {
                "status": "WORKER_BLOCKED" if isinstance(stored_result, dict) and stored_result.get("status") == "BLOCKED" else "ALREADY_COMPLETED",
                "agent_id": agent_id,
                "message_id": message_id,
                "mission_id": mission_id,
                "correlation_id": correlation_id,
                "result": stored_result,
                "durable_receipt": True,
            }

        dispatch = self.runtime.dispatch_one(agent_id)
        if dispatch is None:
            return {
                "status": "QUEUED",
                "agent_id": agent_id,
                "message_id": message_id,
                "mission_id": mission_id,
                "correlation_id": correlation_id,
                "reason": "no_message_dispatched",
            }
        if dispatch.message_id != message_id:
            return {
                "status": "QUEUED",
                "agent_id": agent_id,
                "message_id": message_id,
                "mission_id": mission_id,
                "correlation_id": correlation_id,
                "reason": "older_inbox_message_dispatched_first",
                "dispatched_message_id": dispatch.message_id,
            }
        if dispatch.status != "HANDLED":
            return {
                "status": "HANDLER_FAILED",
                "agent_id": agent_id,
                "message_id": message_id,
                "mission_id": mission_id,
                "correlation_id": correlation_id,
                "error_type": dispatch.error_type,
                "durable_receipt": False,
            }
        worker_blocked = isinstance(dispatch.result, dict) and dispatch.result.get("status") == "BLOCKED"
        return {
            "status": "WORKER_BLOCKED" if worker_blocked else "COMPLETED",
            "agent_id": agent_id,
            "message_id": message_id,
            "mission_id": mission_id,
            "correlation_id": correlation_id,
            "result": dispatch.result,
            "durable_receipt": True,
        }
