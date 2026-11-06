from __future__ import annotations

import json

from core.organization.configured_readonly_workers import (
    REPOSITORIES_ENV,
    WORKSPACE_ROOT_ENV,
    register_configured_readonly_workers,
)


class FakeRuntime:
    def __init__(self):
        self.handlers = {}

    def has_handler(self, agent_id):
        return agent_id in self.handlers

    def register_handler(self, agent_id, handler):
        if agent_id in self.handlers:
            raise ValueError("duplicate")
        self.handlers[agent_id] = handler


def configured(root, repositories=None):
    return {
        WORKSPACE_ROOT_ENV: str(root),
        REPOSITORIES_ENV: json.dumps(repositories or {"dgm-mat": "DGM-MAT"}),
    }


def test_registration_is_disabled_without_explicit_operator_configuration(tmp_path):
    runtime = FakeRuntime()
    result = register_configured_readonly_workers(runtime, environ={})
    assert result["status"] == "DISABLED"
    assert runtime.handlers == {}


def test_registers_only_two_readonly_workers_from_host_allowlist(tmp_path):
    root = tmp_path / "workspace"
    repo = root / "DGM-MAT"
    repo.mkdir(parents=True)
    runtime = FakeRuntime()
    result = register_configured_readonly_workers(runtime, environ=configured(root))
    assert result["status"] == "REGISTERED"
    assert set(result["registered_agents"]) == {
        "agent:repository-cartographer", "agent:python-source-analyst"
    }
    assert result["repository_count"] == 1
    assert result["code_execution_enabled"] is False
    assert result["write_capability_enabled"] is False
    assert result["network_capability_enabled"] is False


def test_invalid_or_escaping_paths_fail_closed(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    runtime = FakeRuntime()
    result = register_configured_readonly_workers(
        runtime, environ=configured(root, {"escape": "../outside"})
    )
    assert result["status"] == "DISABLED"
    assert runtime.handlers == {}


def test_absolute_paths_are_rejected(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    runtime = FakeRuntime()
    result = register_configured_readonly_workers(
        runtime, environ=configured(root, {"absolute": str(root)})
    )
    assert result["status"] == "DISABLED"
    assert runtime.handlers == {}


def test_registration_is_idempotent_for_existing_handlers(tmp_path):
    root = tmp_path / "workspace"
    (root / "DGM-MAT").mkdir(parents=True)
    runtime = FakeRuntime()
    first = register_configured_readonly_workers(runtime, environ=configured(root))
    second = register_configured_readonly_workers(runtime, environ=configured(root))
    assert first["status"] == "REGISTERED"
    assert second["status"] == "ALREADY_REGISTERED"
    assert len(runtime.handlers) == 2
