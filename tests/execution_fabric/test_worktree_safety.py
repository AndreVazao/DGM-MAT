from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from core.execution_fabric.worktree_runtime import WorktreeRuntime


def _git(path: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(path), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _repository(path: Path) -> Path:
    path.mkdir(parents=True)
    _git(path, "init")
    _git(path, "config", "user.email", "tests@example.invalid")
    _git(path, "config", "user.name", "DGM Tests")
    (path / "core").mkdir()
    (path / "core" / "sample.py").write_text("VALUE = 1\n", encoding="utf-8")
    _git(path, "add", ".")
    _git(path, "commit", "-m", "initial")
    return path


def test_create_sandbox_creates_registered_worktree_outside_primary(tmp_path):
    repo = _repository(tmp_path / "repo")
    runtime = WorktreeRuntime(tmp_path / "worktrees", repo_path=repo)
    sandbox = runtime.create_sandbox("mission_123")

    assert sandbox is not None
    assert sandbox.is_dir()
    assert sandbox != repo
    assert runtime._verify_worktree(sandbox)
    assert runtime.cleanup_sandbox("mission_123") is True
    assert not sandbox.exists()


def test_cleanup_preserves_dirty_worktree_for_recovery(tmp_path):
    repo = _repository(tmp_path / "repo")
    runtime = WorktreeRuntime(tmp_path / "worktrees", repo_path=repo)
    sandbox = runtime.create_sandbox("mission_dirty")
    assert sandbox is not None
    (sandbox / "core" / "sample.py").write_text("VALUE = 2\n", encoding="utf-8")

    assert runtime.cleanup_sandbox("mission_dirty") is False
    assert sandbox.exists()
    assert "VALUE = 2" in (sandbox / "core" / "sample.py").read_text(encoding="utf-8")


def test_worktree_runtime_rejects_arbitrary_commands_and_shell_strings(tmp_path):
    repo = _repository(tmp_path / "repo")
    runtime = WorktreeRuntime(tmp_path / "worktrees", repo_path=repo)
    sandbox = runtime.create_sandbox("mission_commands")
    assert sandbox is not None

    assert runtime.execute_in_worktree("dgm-sandbox-mission_commands", "python -c print(1)") is None
    assert runtime.execute_in_worktree(
        "dgm-sandbox-mission_commands", ["python", "-c", "print(1)"]
    ) is None
    assert runtime.cleanup_sandbox("mission_commands") is True


def test_worktree_runtime_rejects_path_traversal_and_invalid_task_ids(tmp_path):
    repo = _repository(tmp_path / "repo")
    runtime = WorktreeRuntime(tmp_path / "worktrees", repo_path=repo)

    assert runtime.create_worktree("../outside") is None
    assert runtime.create_sandbox("../../escape") is None
    assert not (tmp_path / "escape").exists()


def test_worktree_runtime_runs_only_allowlisted_pytest_target(tmp_path):
    repo = _repository(tmp_path / 'repo')
    tests = repo / 'tests'
    tests.mkdir()
    (tests / 'test_ok.py').write_text('def test_ok():\n    assert 2 + 2 == 4\n', encoding='utf-8')
    _git(repo, 'add', 'tests')
    _git(repo, 'commit', '-m', 'add validation test')
    runtime = WorktreeRuntime(tmp_path / 'worktrees', repo_path=repo)
    sandbox = runtime.create_sandbox('mission_validation')
    assert sandbox is not None

    result = runtime.execute_in_worktree(
        'dgm-sandbox-mission_validation',
        ['python', '-m', 'pytest', '-q', 'tests/test_ok.py'],
    )

    assert result is not None
    assert result.returncode == 0
    assert '1 passed' in result.stdout
    assert runtime.cleanup_sandbox('mission_validation') is True


def test_worktree_validation_bounds_captured_output(tmp_path):
    repo = _repository(tmp_path / 'repo')
    tests = repo / 'tests'
    tests.mkdir()
    (tests / 'test_noisy.py').write_text(
        'def test_noisy():\n    print("x" * 20000)\n    assert False\n',
        encoding='utf-8',
    )
    _git(repo, 'add', 'tests')
    _git(repo, 'commit', '-m', 'add noisy validation test')
    runtime = WorktreeRuntime(
        tmp_path / 'worktrees', repo_path=repo, output_limit=1024
    )
    sandbox = runtime.create_sandbox('mission_output')
    assert sandbox is not None

    result = runtime.execute_in_worktree(
        'dgm-sandbox-mission_output',
        ['python', '-m', 'pytest', '-q', 'tests/test_noisy.py'],
    )

    assert result is not None
    assert result.returncode == 1
    assert len(result.stdout) <= 1024
    assert len(result.stderr) <= 1024
    assert runtime.cleanup_sandbox('mission_output') is True


def test_worktree_validation_timeout_is_reported_and_process_is_stopped(tmp_path):
    repo = _repository(tmp_path / 'repo')
    tests = repo / 'tests'
    tests.mkdir()
    (tests / 'test_slow.py').write_text(
        'import time\ndef test_slow():\n    time.sleep(15)\n',
        encoding='utf-8',
    )
    _git(repo, 'add', 'tests')
    _git(repo, 'commit', '-m', 'add slow validation test')
    runtime = WorktreeRuntime(
        tmp_path / 'worktrees', repo_path=repo, command_timeout=5
    )
    sandbox = runtime.create_sandbox('mission_timeout')
    assert sandbox is not None

    result = runtime.execute_in_worktree(
        'dgm-sandbox-mission_timeout',
        ['python', '-m', 'pytest', '-q', 'tests/test_slow.py'],
    )

    assert result is not None
    assert result.returncode == 124
    assert 'timed out' in result.stderr
    assert runtime.cleanup_sandbox('mission_timeout') is True


def test_validation_target_rejects_symlinks_outside_tests_root(tmp_path):
    repo = _repository(tmp_path / 'repo')
    tests = repo / 'tests'
    tests.mkdir()
    outside = tmp_path / 'outside.py'
    outside.write_text('def test_escape():\n    assert True\n', encoding='utf-8')
    link = tests / 'test_escape.py'
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip('Symlink creation is not permitted on this Windows configuration.')

    runtime = WorktreeRuntime(tmp_path / 'worktrees', repo_path=repo)
    assert runtime._safe_test_target(repo, 'tests/test_escape.py') is False


def test_cleanup_preserves_ignored_worktree_data_for_recovery(tmp_path):
    repo = _repository(tmp_path / "repo")
    (repo / ".gitignore").write_text("*.secret\\n", encoding="utf-8")
    _git(repo, "add", ".gitignore")
    _git(repo, "commit", "-m", "ignore local secret files")
    runtime = WorktreeRuntime(tmp_path / "worktrees", repo_path=repo)
    sandbox = runtime.create_sandbox("mission_ignored")
    assert sandbox is not None
    ignored_file = sandbox / "local.secret"
    ignored_file.write_text("recoverable local data", encoding="utf-8")

    assert runtime.cleanup_sandbox("mission_ignored") is False
    assert sandbox.exists()
    assert ignored_file.read_text(encoding="utf-8") == "recoverable local data"


def test_validation_runner_does_not_inherit_secret_environment(tmp_path, monkeypatch):
    repo = _repository(tmp_path / "repo")
    tests = repo / "tests"
    tests.mkdir()
    (tests / "test_environment.py").write_text(
        """import os
def test_secret_not_inherited():
    assert 'DGM_TEST_SECRET' not in os.environ
""",
        encoding="utf-8",
    )
    _git(repo, "add", "tests")
    _git(repo, "commit", "-m", "add validation environment test")
    monkeypatch.setenv("DGM_TEST_SECRET", "must-not-leak-to-validation")
    runtime = WorktreeRuntime(tmp_path / "worktrees", repo_path=repo)
    sandbox = runtime.create_sandbox("mission_env")
    assert sandbox is not None

    result = runtime.execute_in_worktree(
        "dgm-sandbox-mission_env",
        ["python", "-m", "pytest", "-q", "tests/test_environment.py"],
    )

    assert result is not None
    assert result.returncode == 0
    assert "1 passed" in result.stdout
    assert runtime.cleanup_sandbox("mission_env") is True
