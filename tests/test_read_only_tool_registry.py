from __future__ import annotations

import pytest

from core.operations.command_executor import CommandDenied, CommandExecutor
from core.operations.read_only_tool_registry import ReadOnlyToolRegistry


class FakeResult:
    returncode = 0
    stdout = "read-only-result"
    stderr = ""


def make_registry(tmp_path, *, runner=None, which=None):
    executor = CommandExecutor(
        allowed_roots=[tmp_path],
        runner=runner or (lambda *args, **kwargs: FakeResult()),
        which=which or (lambda name: "/usr/bin/" + name),
        platform="posix",
    )
    return ReadOnlyToolRegistry(executor)


def test_registry_exposes_only_the_existing_fixed_catalog(tmp_path):
    registry = make_registry(tmp_path)
    descriptors = registry.list_tools()

    assert [item.name for item in descriptors] == [
        "system.summary",
        "process.top",
        "engines.inventory",
        "git.status",
        "ollama.status",
        "claude.status",
    ]
    assert all(item.risk_class == "LOW" for item in descriptors)
    assert all(item.approval_policy == "REQUIRED" for item in descriptors)
    assert all(item.allowed_transports == ["local"] for item in descriptors)


def test_descriptor_schema_is_strict_and_target_is_required_only_for_git(tmp_path):
    registry = make_registry(tmp_path)
    git = registry.get_tool("git.status")
    system = registry.get_tool("system.summary")

    assert git.input_schema["required"] == ["target_path"]
    assert git.input_schema["additionalProperties"] is False
    assert system.input_schema["required"] == []
    assert system.input_schema["properties"] == {}


def test_unknown_tool_is_not_synthesized_or_dispatched(tmp_path):
    registry = make_registry(tmp_path)
    with pytest.raises(CommandDenied, match="not registered"):
        registry.get_tool("shell.execute")
    with pytest.raises(CommandDenied, match="not registered"):
        registry.execute("shell.execute", {"command": "whoami"})


@pytest.mark.parametrize(
    "arguments",
    [
        {"command": "whoami"},
        {"shell": True},
        {"target_path": "C:/tmp"},
        {"timeout": 999999},
    ],
)
def test_non_target_tools_reject_every_argument(tmp_path, arguments):
    registry = make_registry(tmp_path)
    with pytest.raises(CommandDenied, match="unsupported fields"):
        registry.execute("system.summary", arguments)


def test_target_tool_requires_nonempty_string_target(tmp_path):
    registry = make_registry(tmp_path)
    for arguments in ({}, {"target_path": ""}, {"target_path": None}, {"target_path": 42}):
        with pytest.raises(CommandDenied):
            registry.execute("git.status", arguments)


def test_target_tool_rejects_extra_fields_before_executor(tmp_path):
    registry = make_registry(tmp_path)
    with pytest.raises(CommandDenied, match="unsupported fields"):
        registry.execute("git.status", {"target_path": str(tmp_path), "command": "status"})


def test_git_dispatch_delegates_structured_target_to_existing_executor(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    calls = []

    def runner(argv, **kwargs):
        calls.append((argv, kwargs))
        return FakeResult()

    registry = make_registry(tmp_path, runner=runner, which=lambda name: "/usr/bin/git")
    result = registry.execute("git.status", {"target_path": str(repo)})

    assert result["status"] == "passed"
    assert result["command_id"] == "git.status"
    assert calls[0][1]["shell"] is False
    assert calls[0][0][-3:] == ["status", "--short", "--branch"]


def test_git_dispatch_keeps_existing_allowed_root_boundary(tmp_path):
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / ".git").mkdir()
    registry = make_registry(allowed)

    with pytest.raises(CommandDenied, match="outside"):
        registry.execute("git.status", {"target_path": str(outside)})


def test_descriptor_mutation_does_not_change_registry_catalog(tmp_path):
    registry = make_registry(tmp_path)
    descriptor = registry.get_tool("system.summary")
    descriptor.capabilities.append("shell.execute")

    fresh = registry.get_tool("system.summary")
    assert "shell.execute" not in fresh.capabilities
