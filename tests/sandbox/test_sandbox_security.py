from __future__ import annotations

import subprocess
from pathlib import Path

from core.execution_fabric.worktree_runtime import WorktreeRuntime
from core.sandbox.isolated_runtime import IsolatedRuntime


def _git(path: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(path), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _repo(path: Path, *, with_test: bool = False) -> Path:
    path.mkdir(parents=True)
    _git(path, "init")
    _git(path, "config", "user.email", "tests@example.invalid")
    _git(path, "config", "user.name", "DGM Tests")
    (path / "core").mkdir()
    (path / "core" / "sample.py").write_text("VALUE = 1\n", encoding="utf-8")
    if with_test:
        (path / "tests").mkdir()
        (path / "tests" / "test_ok.py").write_text(
            "def test_ok():\n    assert 2 + 2 == 4\n", encoding="utf-8"
        )
    _git(path, "add", ".")
    _git(path, "commit", "-m", "initial")
    return path


def test_isolated_runtime_creates_and_removes_registered_worktree(tmp_path):
    repo = _repo(tmp_path / "repo")
    runtime = IsolatedRuntime(WorktreeRuntime(tmp_path / "worktrees", repo_path=repo))

    sandbox = Path(runtime.create_sandbox("test_task"))

    assert sandbox.name == "dgm-sandbox-test_task"
    assert sandbox.is_dir()
    assert runtime.rollback_sandbox("test_task") is True
    assert not sandbox.exists()


def test_isolated_runtime_delegates_only_allowlisted_validation(tmp_path):
    repo = _repo(tmp_path / "repo", with_test=True)
    runtime = IsolatedRuntime(WorktreeRuntime(tmp_path / "worktrees", repo_path=repo))
    sandbox = runtime.create_sandbox("safe_task")

    accepted = runtime.run_safe(
        sandbox,
        ["python", "-m", "pytest", "-q", "tests/test_ok.py"],
        "safe_task",
    )
    rejected = runtime.run_safe(
        sandbox,
        ["python", "-c", "print('not allowed')"],
        "safe_task",
    )

    assert accepted["status"] == "success"
    assert accepted["exit_code"] == 0
    assert rejected["status"] == "rejected"
    assert runtime.rollback_sandbox("safe_task") is True


def test_isolated_runtime_refuses_mismatched_sandbox_path(tmp_path):
    repo = _repo(tmp_path / "repo", with_test=True)
    runtime = IsolatedRuntime(WorktreeRuntime(tmp_path / "worktrees", repo_path=repo))
    sandbox = runtime.create_sandbox("path_task")

    result = runtime.run_safe(
        str(tmp_path),
        ["python", "-m", "pytest", "-q", "tests/test_ok.py"],
        "path_task",
    )

    assert result["status"] == "rejected"
    assert runtime.rollback_sandbox("path_task") is True


def test_execution_limits():
    from core.sandbox.execution_limits import ExecutionLimits

    limits = ExecutionLimits()
    assert limits.check_limits({"cpu": 50})
    assert not limits.check_limits({"cpu": 95})
