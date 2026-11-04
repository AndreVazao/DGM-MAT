from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from core.execution_fabric.worktree_runtime import WorktreeRuntime
from core.execution_fabric.safe_patch_engine import SafePatchEngine


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


def test_safe_patch_engine_applies_only_to_registered_worktree(tmp_path):
    repo = _repository(tmp_path / "repo")
    runtime = WorktreeRuntime(tmp_path / "worktrees", repo_path=repo)
    sandbox = runtime.create_sandbox("mission_patch")
    assert sandbox is not None
    engine = SafePatchEngine(repository_root=repo)
    patch = (
        "--- a/core/sample.py\n"
        "+++ b/core/sample.py\n"
        "@@ -1 +1 @@\n"
        "-VALUE = 1\n"
        "+VALUE = 2\n"
    )

    engine.apply_patch(patch, sandbox)

    assert (sandbox / "core" / "sample.py").read_text(encoding="utf-8") == "VALUE = 2\n"
    assert (repo / "core" / "sample.py").read_text(encoding="utf-8") == "VALUE = 1\n"
    assert runtime.cleanup_sandbox("mission_patch") is False


def test_safe_patch_engine_rejects_primary_repo_and_escaping_paths(tmp_path):
    repo = _repository(tmp_path / "repo")
    engine = SafePatchEngine(repository_root=repo)
    patch = "--- a/core/sample.py\n+++ b/core/sample.py\n@@ -1 +1 @@\n-VALUE = 1\n+VALUE = 2\n"

    with pytest.raises(ValueError, match="primary repository"):
        engine.apply_patch(patch, repo)
    with pytest.raises(ValueError, match="escaping"):
        engine._validate_patch_paths(
            "--- a/../../outside.txt\n+++ b/../../outside.txt\n"
        )


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


def test_patch_generation_includes_tracked_changes_and_rejects_untracked_files(tmp_path):
    repo = _repository(tmp_path / 'repo')
    runtime = WorktreeRuntime(tmp_path / 'worktrees', repo_path=repo)
    sandbox = runtime.create_sandbox('mission_diff')
    assert sandbox is not None
    engine = SafePatchEngine(repository_root=repo)

    (sandbox / 'core' / 'sample.py').write_text('VALUE = 7\n', encoding='utf-8')
    patch = engine.generate_patch(sandbox)
    assert 'VALUE = 7' in patch

    (sandbox / 'core' / 'new_module.py').write_text('NEW_VALUE = 1\n', encoding='utf-8')
    with pytest.raises(ValueError, match='Untracked files'):
        engine.generate_patch(sandbox)
    assert runtime.cleanup_sandbox('mission_diff') is False


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
