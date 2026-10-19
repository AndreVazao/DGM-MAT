from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from core.operations.command_executor import CommandDenied, CommandExecutor


class FakeCompleted:
    def __init__(self, returncode=0, stdout="ok", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    (repo / ".git").mkdir()
    return repo


def test_catalog_does_not_offer_arbitrary_shell_or_elevation():
    executor = CommandExecutor(allowed_roots=[])
    catalog = executor.catalog()
    assert catalog["arbitrary_shell"] is False
    assert catalog["administrator_elevation"] is False
    assert {item["id"] for item in catalog["commands"]} >= {"system.summary", "git.status", "engines.inventory"}


def test_unknown_command_is_denied():
    executor = CommandExecutor(allowed_roots=[])
    with pytest.raises(CommandDenied):
        executor.execute("powershell.raw", target_path="C:/tmp")


def test_git_status_requires_target(tmp_path):
    executor = CommandExecutor(allowed_roots=[tmp_path], which=lambda name: "/usr/bin/git")
    with pytest.raises(CommandDenied):
        executor.execute("git.status")


def test_git_target_must_be_inside_allowed_root(tmp_path):
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    outside_parent = tmp_path / "outside-parent"
    outside_parent.mkdir()
    outside = make_repo(outside_parent)
    executor = CommandExecutor(allowed_roots=[allowed], which=lambda name: "/usr/bin/git")
    with pytest.raises(CommandDenied):
        executor.execute("git.status", target_path=str(outside))


def test_git_status_uses_no_shell_and_structured_args(tmp_path):
    repo = make_repo(tmp_path)
    calls = []

    def runner(argv, **kwargs):
        calls.append((argv, kwargs))
        return FakeCompleted(0, "## feature/test", "")

    executor = CommandExecutor(allowed_roots=[tmp_path], runner=runner, which=lambda name: "/usr/bin/git")
    result = executor.execute("git.status", target_path=str(repo))
    assert result["status"] == "passed"
    assert calls[0][1]["shell"] is False
    assert calls[0][0][-3:] == ["status", "--short", "--branch"]


def test_output_is_bounded_for_stdout_and_stderr(tmp_path):
    repo = make_repo(tmp_path)
    executor = CommandExecutor(
        allowed_roots=[tmp_path],
        runner=lambda *a, **k: FakeCompleted(stdout="x" * 5000, stderr="y" * 5000),
        which=lambda name: "/usr/bin/git",
        output_limit=512,
    )
    result = executor.execute("git.status", target_path=str(repo))
    assert len(result["stdout"]) == 512
    assert len(result["stderr"]) == 512


def test_timeout_is_reported(tmp_path):
    def timeout_runner(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], 1, output="partial")

    executor = CommandExecutor(allowed_roots=[tmp_path], runner=timeout_runner, which=lambda name: "/usr/bin/git")
    repo = make_repo(tmp_path)
    result = executor.execute("git.status", target_path=str(repo))
    assert result["status"] == "timeout"
    assert result["returncode"] is None


def test_claude_status_is_read_only_version_probe(tmp_path):
    calls = []

    def runner(argv, **kwargs):
        calls.append((argv, kwargs))
        return FakeCompleted(0, "2.1.112", "")

    executor = CommandExecutor(
        allowed_roots=[tmp_path], runner=runner,
        which=lambda name: "/tools/claude" if name == "claude" else None,
    )
    result = executor.execute("claude.status")
    assert result["status"] == "passed"
    assert calls[0][0] == ["/tools/claude", "--version"]
    assert calls[0][1]["shell"] is False


def test_ollama_missing_is_reported_without_starting_process(tmp_path):
    calls = []
    executor = CommandExecutor(
        allowed_roots=[tmp_path],
        runner=lambda *a, **k: calls.append((a, k)),
        which=lambda name: None,
    )
    result = executor.execute("ollama.status")
    assert result["status"] == "unavailable"
    assert calls == []


def test_system_summary_uses_fixed_powershell_script_and_no_shell(tmp_path):
    calls = []

    def runner(argv, **kwargs):
        calls.append((argv, kwargs))
        return FakeCompleted(0, '{"PowerShell":"5.1"}', "")

    executor = CommandExecutor(
        allowed_roots=[tmp_path], runner=runner,
        which=lambda name: "/windows/powershell.exe" if name == "powershell" else None,
    )
    result = executor.execute("system.summary")
    assert result["status"] == "passed"
    assert calls[0][0][:5] == [
        "/windows/powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive", "-Command"
    ]
    assert "PowerShell=$PSVersionTable.PSVersion.ToString()" in calls[0][0][5]
    assert calls[0][1]["shell"] is False


def test_engine_inventory_only_returns_process_names_and_ids(tmp_path):
    calls = []

    def runner(argv, **kwargs):
        calls.append((argv, kwargs))
        return FakeCompleted(0, '[{"Name":"ollama.exe","ProcessId":123}]', "")

    executor = CommandExecutor(
        allowed_roots=[tmp_path], runner=runner,
        which=lambda name: "/windows/powershell.exe" if name == "powershell" else None,
    )
    result = executor.execute("engines.inventory")
    assert result["status"] == "passed"
    script = calls[0][0][5]
    assert "Select-Object Name,ProcessId" in script
    assert "CommandLine" in script  # used only for filtering, never selected/returned
    assert "Select-Object Name,ProcessId,CommandLine" not in script
    assert calls[0][1]["shell"] is False


def test_no_existing_allowed_root_fails_closed(tmp_path):
    missing_root = tmp_path / "not-created"
    executor = CommandExecutor(
        allowed_roots=[missing_root],
        runner=lambda *a, **k: pytest.fail("runner must not be invoked"),
        which=lambda name: "/tools/claude" if name == "claude" else None,
    )
    with pytest.raises(CommandDenied, match="No configured allowed root exists"):
        executor.execute("claude.status")


def test_os_error_message_is_not_returned(tmp_path):
    def failing_runner(*args, **kwargs):
        raise OSError("sensitive local path C:/Users/person/private.txt")

    executor = CommandExecutor(
        allowed_roots=[tmp_path], runner=failing_runner,
        which=lambda name: "/tools/claude" if name == "claude" else None,
    )
    result = executor.execute("claude.status")
    assert result["status"] == "failed"
    assert result["stderr"] == "OSError"
    assert "private.txt" not in result["stderr"]


def test_git_target_with_invalid_path_characters_is_denied(tmp_path):
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    executor = CommandExecutor(
        allowed_roots=[allowed],
        runner=lambda *a, **k: pytest.fail("runner must not be invoked"),
        which=lambda name: "/usr/bin/git",
    )
    with pytest.raises(CommandDenied, match="Target path is invalid"):
        executor.execute("git.status", target_path="bad\x00path")
