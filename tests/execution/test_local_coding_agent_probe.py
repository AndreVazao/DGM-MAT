from pathlib import Path
import subprocess

import pytest

from core.execution import local_coding_agent_probe as probe_module
from core.execution.local_coding_agent_probe import LocalCodingAgentProbe


def test_missing_local_agents_are_reported_independently(monkeypatch):
    monkeypatch.setattr(probe_module.shutil, "which", lambda _command: None)
    results = LocalCodingAgentProbe().probe_all()

    assert set(results) == {"codex", "claude_code"}
    assert results["codex"]["status"] == "not_installed"
    assert results["claude_code"]["status"] == "not_installed"
    assert results["codex"]["execution_enabled"] is False
    assert results["claude_code"]["identity_verified"] is False


def test_probe_runs_only_fixed_version_command_without_shell_or_secret_environment(
    monkeypatch, tmp_path
):
    executable = tmp_path / "codex"
    executable.write_text("#!/bin/sh\necho 'codex-cli 1.2.3'\n", encoding="utf-8")
    executable.chmod(0o755)
    monkeypatch.setattr(probe_module.shutil, "which", lambda command: str(executable) if command == "codex" else None)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "must-not-leak")
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-leak-either")
    monkeypatch.setenv("DGM_FCC_BASE_URL", "http://127.0.0.1:8082")

    captured = {}

    def fake_run(args, **kwargs):
        captured["args"] = args
        captured.update(kwargs)
        return subprocess.CompletedProcess(args, 0, stdout="codex-cli 1.2.3\n", stderr="")

    monkeypatch.setattr(probe_module.subprocess, "run", fake_run)
    result = LocalCodingAgentProbe().probe_agent("codex")

    assert result.status == "available"
    assert result.version == "codex-cli 1.2.3"
    assert captured["args"] == [str(executable.resolve()), "--version"]
    assert captured["shell"] is False
    assert captured["timeout"] == 5
    assert "ANTHROPIC_API_KEY" not in captured["env"]
    assert "OPENAI_API_KEY" not in captured["env"]
    assert "must-not-leak" not in str(result.to_dict())
    assert result.configured_endpoint_env_names == ("DGM_FCC_BASE_URL",)
    assert result.billing_verified is False
    assert result.execution_enabled is False


def test_version_output_is_bounded_and_control_characters_are_removed(monkeypatch, tmp_path):
    executable = tmp_path / "claude"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o755)
    monkeypatch.setattr(probe_module.shutil, "which", lambda _command: str(executable))
    monkeypatch.setattr(
        probe_module.subprocess,
        "run",
        lambda args, **kwargs: subprocess.CompletedProcess(
            args, 0, stdout="Claude\x00 Code 2.1.0\n" + ("x" * 500), stderr=""
        ),
    )

    result = LocalCodingAgentProbe().probe_agent("claude_code")

    assert result.status == "available"
    assert "\x00" not in result.version
    assert len(result.version) <= LocalCodingAgentProbe.MAX_VERSION_CHARS


def test_timeout_is_reported_without_exposing_process_output(monkeypatch, tmp_path):
    executable = tmp_path / "claude"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o755)
    monkeypatch.setattr(probe_module.shutil, "which", lambda _command: str(executable))

    def timeout(*_args, **_kwargs):
        raise subprocess.TimeoutExpired("claude", 5, output="private output")

    monkeypatch.setattr(probe_module.subprocess, "run", timeout)
    result = LocalCodingAgentProbe().probe_agent("claude_code")

    assert result.available is True
    assert result.status == "version_probe_timeout"
    assert result.probe_error == "timeout"
    assert "private output" not in str(result.to_dict())


def test_nonzero_version_probe_does_not_claim_agent_ready(monkeypatch, tmp_path):
    executable = tmp_path / "codex"
    executable.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    executable.chmod(0o755)
    monkeypatch.setattr(probe_module.shutil, "which", lambda _command: str(executable))
    monkeypatch.setattr(
        probe_module.subprocess,
        "run",
        lambda args, **kwargs: subprocess.CompletedProcess(args, 7, stdout="", stderr="private diagnostic"),
    )

    result = LocalCodingAgentProbe().probe_agent("codex")

    assert result.available is True
    assert result.status == "version_probe_failed"
    assert result.probe_error == "exit_code_7"
    assert "private diagnostic" not in str(result.to_dict())


def test_unknown_agent_id_is_rejected_before_any_process_lookup(monkeypatch):
    monkeypatch.setattr(
        probe_module.shutil,
        "which",
        lambda _command: pytest.fail("unsupported agent must not trigger PATH lookup"),
    )
    with pytest.raises(ValueError, match="Unsupported local coding agent"):
        LocalCodingAgentProbe().probe_agent("unknown-cli")


@pytest.mark.parametrize("timeout", [0, 16, True, "5"])
def test_probe_timeout_is_strictly_validated(timeout):
    with pytest.raises(ValueError):
        LocalCodingAgentProbe(timeout_seconds=timeout)


def test_windows_npm_powershell_shim_is_found_and_invoked_without_profile(monkeypatch, tmp_path):
    appdata = tmp_path / "Roaming"
    npm = appdata / "npm"
    npm.mkdir(parents=True)
    shim = npm / "claude.ps1"
    shim.write_text("Write-Output 'Claude Code 2.1.0'\n", encoding="utf-8")
    monkeypatch.setattr(LocalCodingAgentProbe, "_is_windows", staticmethod(lambda: True))
    monkeypatch.setenv("APPDATA", str(appdata))
    monkeypatch.setattr(
        probe_module.shutil,
        "which",
        lambda command: "C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe" if command == "powershell" else None,
    )
    captured = {}

    def fake_run(args, **kwargs):
        captured["args"] = args
        captured.update(kwargs)
        return subprocess.CompletedProcess(args, 0, stdout="Claude Code 2.1.0\n", stderr="")

    monkeypatch.setattr(probe_module.subprocess, "run", fake_run)
    result = LocalCodingAgentProbe().probe_agent("claude_code")

    assert result.status == "available"
    assert result.version == "Claude Code 2.1.0"
    assert captured["args"] == [
        "C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe",
        "-NoLogo", "-NoProfile", "-NonInteractive", "-File", str(shim.resolve()), "--version",
    ]
    assert captured["shell"] is False


def test_windows_powershell_shim_fails_closed_without_interpreter(monkeypatch, tmp_path):
    appdata = tmp_path / "Roaming"
    npm = appdata / "npm"
    npm.mkdir(parents=True)
    shim = npm / "codex.ps1"
    shim.write_text("Write-Output 'Codex CLI'\n", encoding="utf-8")
    monkeypatch.setattr(LocalCodingAgentProbe, "_is_windows", staticmethod(lambda: True))
    monkeypatch.setenv("APPDATA", str(appdata))
    monkeypatch.delenv("COMSPEC", raising=False)
    monkeypatch.setattr(probe_module.shutil, "which", lambda _command: None)
    monkeypatch.setattr(
        probe_module.subprocess,
        "run",
        lambda *_args, **_kwargs: pytest.fail("No interpreter means no process launch"),
    )

    result = LocalCodingAgentProbe().probe_agent("codex")

    assert result.available is True
    assert result.status == "version_probe_unavailable"
    assert result.probe_error == "safe_interpreter_unavailable"


def test_windows_cmd_shim_is_detected_but_never_executed(monkeypatch, tmp_path):
    appdata = tmp_path / "Roaming"
    npm = appdata / "npm"
    npm.mkdir(parents=True)
    shim = npm / "codex.cmd"
    shim.write_text("@echo off\\necho Codex CLI 1.0.0\\n", encoding="utf-8")
    monkeypatch.setattr(LocalCodingAgentProbe, "_is_windows", staticmethod(lambda: True))
    monkeypatch.setenv("APPDATA", str(appdata))
    monkeypatch.setattr(probe_module.shutil, "which", lambda _command: str(shim))
    monkeypatch.setattr(
        probe_module.subprocess,
        "run",
        lambda *_args, **_kwargs: pytest.fail("cmd.exe wrappers must never be launched"),
    )

    result = LocalCodingAgentProbe().probe_agent("codex")

    assert result.available is True
    assert result.status == "version_probe_unavailable"
    assert result.probe_error == "cmd_wrapper_not_executed_for_safety"
    assert result.executable_path == str(shim.resolve())


def test_windows_exe_is_preferred_over_cmd_wrapper(monkeypatch, tmp_path):
    appdata = tmp_path / "Roaming"
    npm = appdata / "npm"
    npm.mkdir(parents=True)
    exe = npm / "codex.exe"
    exe.write_bytes(b"fixture")
    cmd = npm / "codex.cmd"
    cmd.write_text("@echo off\\n", encoding="utf-8")
    monkeypatch.setattr(LocalCodingAgentProbe, "_is_windows", staticmethod(lambda: True))
    monkeypatch.setenv("APPDATA", str(appdata))
    captured = {}

    def fake_run(args, **kwargs):
        captured["args"] = args
        captured.update(kwargs)
        return subprocess.CompletedProcess(args, 0, stdout="Codex CLI 1.0.0\\n", stderr="")

    monkeypatch.setattr(probe_module.subprocess, "run", fake_run)
    result = LocalCodingAgentProbe().probe_agent("codex")

    assert result.status == "available"
    assert captured["args"] == [str(exe.resolve()), "--version"]
    assert captured["shell"] is False
