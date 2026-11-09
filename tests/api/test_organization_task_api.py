from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.organization.models import Task, TaskStatus
import core.api.runtime_api as runtime_api


@dataclass
class FakeApproval:
    status: str
    diff: str


class FakeApprovalManager:
    records: dict[str, FakeApproval] = {}

    @property
    def approvals(self):
        return self.records

    def request_approval(self, task_id, diff, risk_score=0.0, impact="LOW"):
        self.records.setdefault(task_id, FakeApproval("awaiting_approval", diff))
        return {"task_id": task_id}

    def approve(self, task_id):
        item = self.records.get(task_id)
        if not item or item.status != "awaiting_approval":
            return False
        item.status = "approved"
        return True

    def reject(self, task_id, reason=""):
        item = self.records.get(task_id)
        if not item or item.status != "awaiting_approval":
            return False
        item.status = "rejected"
        return True


class FakeMissionEngine:
    def __init__(self):
        self.tasks = {}

    def create_organization_task(self, task):
        self.tasks[task.task_id] = task
        return task

    def get_organization_task(self, task_id):
        return self.tasks.get(task_id)

    def delegate_organization_task(self, task_id):
        task = self.tasks[task_id]
        task.assigned_agent = "agent:repository-cartographer"
        task.status = TaskStatus.ASSIGNED
        return SimpleNamespace(agent_id=task.assigned_agent, reason=None)

    def dispatch_organization_task(self, task_id):
        task = self.tasks[task_id]
        task.status = TaskStatus.COMPLETED
        task.metadata["worker_execution"] = {
            "message_id": "msg:worker-receipt-001",
            "durable_receipt": True,
            "result": {"files": 12, "status": "inventory_complete"},
        }
        return {
            "status": "COMPLETED",
            "task_id": task_id,
            "message_id": "msg:worker-receipt-001",
            "durable_receipt": True,
            "result": task.metadata["worker_execution"]["result"],
        }

    def handle_approval_decision(self, approval_id, decision):
        manager = FakeApprovalManager()
        return manager.approve(approval_id) if decision == "approve" else manager.reject(approval_id)


def setup_client(monkeypatch):
    FakeApprovalManager.records = {}
    engine = FakeMissionEngine()
    monkeypatch.setattr(runtime_api, "mission_engine", engine)
    monkeypatch.setattr(runtime_api, "ApprovalManager", FakeApprovalManager)
    app = FastAPI()
    app.include_router(runtime_api.router)
    return TestClient(app), engine


def test_organization_task_command_returns_durable_correlated_result(monkeypatch):
    client, engine = setup_client(monkeypatch)
    response = client.post(
        "/runtime/organization/tasks",
        json={"task_kind": "repository_inventory", "repository_id": "demo"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "COMPLETED"
    task = body["task"]
    assert task["task_id"] in engine.tasks
    assert task["assigned_agent"] == "agent:repository-cartographer"
    assert task["durable_receipt"] is True
    assert task["message_id"] == "msg:worker-receipt-001"
    assert task["result"] == {"files": 12, "status": "inventory_complete"}
    assert len(task["result_sha256"]) == 64

    fetched = client.get(f"/runtime/organization/tasks/{task['task_id']}")
    assert fetched.status_code == 200
    assert fetched.json()["result_sha256"] == task["result_sha256"]


def test_organization_result_approval_is_bound_to_exact_result_digest(monkeypatch):
    client, _engine = setup_client(monkeypatch)
    created = client.post(
        "/runtime/organization/tasks",
        json={"task_kind": "repository_inventory", "repository_id": "demo"},
    ).json()["task"]
    task_id = created["task_id"]
    digest = created["result_sha256"]

    requested = client.post(
        f"/runtime/organization/tasks/{task_id}/approval",
        json={"result_sha256": digest},
    )
    assert requested.status_code == 201
    approval_id = requested.json()["approval_id"]
    assert requested.json()["status"] == "awaiting_approval"

    stale = client.post(
        f"/runtime/organization/tasks/{task_id}/decision",
        json={"decision": "approve", "result_sha256": "0" * 64},
    )
    assert stale.status_code == 409
    assert FakeApprovalManager.records[approval_id].status == "awaiting_approval"

    decided = client.post(
        f"/runtime/organization/tasks/{task_id}/decision",
        json={"decision": "approve", "result_sha256": digest},
    )
    assert decided.status_code == 200
    assert decided.json()["status"] == "approved"
    assert decided.json()["result_sha256"] == digest

    refreshed = client.get(f"/runtime/organization/tasks/{task_id}")
    assert refreshed.json()["approval_status"] == "approved"


def test_organization_task_command_rejects_free_form_or_unknown_task_kinds(monkeypatch):
    client, engine = setup_client(monkeypatch)
    response = client.post(
        "/runtime/organization/tasks",
        json={
            "task_kind": "run_shell",
            "repository_id": "demo",
            "command": "del *",
        },
    )
    assert response.status_code == 422
    assert engine.tasks == {}


def test_organization_task_command_rejects_invalid_repository_identifiers(monkeypatch):
    client, engine = setup_client(monkeypatch)
    response = client.post(
        "/runtime/organization/tasks",
        json={"task_kind": "repository_inventory", "repository_id": "../outside"},
    )
    assert response.status_code == 422
    assert engine.tasks == {}


def test_organization_task_can_resume_after_a_queued_dispatch(monkeypatch):
    client, engine = setup_client(monkeypatch)
    original_dispatch = engine.dispatch_organization_task
    calls = {"count": 0}

    def delayed_dispatch(task_id):
        calls["count"] += 1
        if calls["count"] == 1:
            return {"status": "QUEUED", "task_id": task_id, "reason": "older_message_pending"}
        return original_dispatch(task_id)

    engine.dispatch_organization_task = delayed_dispatch
    created = client.post(
        "/runtime/organization/tasks",
        json={"task_kind": "repository_inventory", "repository_id": "demo"},
    )
    assert created.status_code == 201
    task_id = created.json()["task"]["task_id"]
    assert created.json()["status"] == "QUEUED"
    assert created.json()["task"]["durable_receipt"] is False

    resumed = client.post(f"/runtime/organization/tasks/{task_id}/dispatch")
    assert resumed.status_code == 200
    assert resumed.json()["status"] == "COMPLETED"
    assert resumed.json()["task"]["durable_receipt"] is True
    assert calls["count"] == 2
