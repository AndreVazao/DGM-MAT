from __future__ import annotations

import subprocess

import pytest

from core.execution.coding_agent_dry_run import (
    CodingAgentDryRunBlocked,
    CodingAgentDryRunPlanner,
    CodingAgentDryRunRequest,
)


@pytest.fixture
def repository(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", str(root)], check=True, capture_output=True)
    return root


def _request(repository, **overrides):
    values = {
        "task_id": "pilot-001",
        "provider": "codex",
        "repository_id": "DGM-MAT",
        "repository_root": str(repository),
        "worktree_root": str(repository.parent / "isolated-worktrees"),
        "base_commit": "a" * 40,
        "goal": "Inspect the mission executor and identify the next safe integration step.",
        "cli_version": "codex 1.0.0",
    }
    values.update(overrides)
    return CodingAgentDryRunRequest(**values)


@pytest.mark.parametrize("provider", ["codex", "claude_code"])
def test_dry_run_builds_fixed_read_only_argv_without_launch(repository, provider):
    planner = CodingAgentDryRunPlanner({"DGM-MAT": str(repository)})
    plan = planner.plan(_request(repository, provider=provider))
    assert plan.launch_enabled is False
    assert plan.access_mode == "read_only"
    assert plan.network_isolation_verified is False
    assert plan.provider_controls_verified is False
    assert plan.network_allowed is (False if provider == "codex" else None)
    assert plan.write_allowed is False
    assert plan.cwd == str(repository.resolve())
    assert plan.request_sha256 and len(plan.request_sha256) == 64
    if provider == "codex":
        assert "--ignore-user-config" in plan.argv
    assert "--dangerously-bypass-approvals-and-sandbox" not in plan.argv
    assert "--dangerously-skip-permissions" not in plan.argv
    assert "--sandbox" in plan.argv if provider == "codex" else "--permission-mode" in plan.argv


def test_request_fingerprint_changes_when_goal_changes(repository):
    planner = CodingAgentDryRunPlanner({"DGM-MAT": str(repository)})
    first = planner.plan(_request(repository))
    second = planner.plan(_request(repository, goal="A different read-only analysis"))
    assert first.request_sha256 != second.request_sha256


@pytest.mark.parametrize(
    "overrides",
    [
        {"repository_id": "other-repo"},
        {"repository_root": "/tmp/not-the-allowlisted-repository"},
        {"base_commit": "main"},
        {"task_id": "../escape"},
        {"goal": ""},
        {"goal": "x" * 4001},
        {"cli_version": ""},
        {"max_turns": 11},
        {"provider": "shell"},
    ],
)
def test_invalid_or_untrusted_request_is_blocked(repository, overrides):
    planner = CodingAgentDryRunPlanner({"DGM-MAT": str(repository)})
    with pytest.raises(CodingAgentDryRunBlocked):
        planner.plan(_request(repository, **overrides))


def test_worktree_root_cannot_overlap_canonical_repository(repository):
    planner = CodingAgentDryRunPlanner({"DGM-MAT": str(repository)})
    with pytest.raises(CodingAgentDryRunBlocked, match="separate"):
        planner.plan(_request(repository, worktree_root=str(repository / ".runtime")))


def test_missing_allowlist_is_blocked():
    with pytest.raises(CodingAgentDryRunBlocked):
        CodingAgentDryRunPlanner({})
