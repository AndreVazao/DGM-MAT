from types import SimpleNamespace

from core.autonomy.mission_engine import MissionEngine


def test_list_repositories_mission_includes_github_portfolio(monkeypatch):
    local = [{"name": "demo", "path": "C:/workspace/demo"}]
    portfolio = {
        "github_api_available": True,
        "summary": {
            "local_repositories": 1,
            "github_repositories": 1,
            "matched_repositories": 1,
            "local_only": 0,
            "github_only": 0,
            "default_branch_synced": 1,
            "default_branch_behind": 0,
            "default_branch_ahead": 0,
            "default_branch_diverged": 0,
            "origin_mismatch": 0,
            "origin_credentials_present": 0,
            "branches_synced": 1,
            "branches_commit_mismatch_review": 0,
            "local_only_branches": 0,
            "github_only_branches": 0,
        },
        "matched": [{
            "name": "demo",
            "origin": "https://github.com/AndreVazao/demo.git",
            "origin_matches_github": True,
            "origin_credentials_present": False,
            "default_branch_comparison": {"status": "SYNCED", "branch": "main"},
        }],
        "local_only": [],
        "github_only": [],
    }

    class FakePortfolio:
        def __init__(self, **kwargs):
            assert kwargs["timeout"] == 20

        def build_inventory(self, repositories):
            assert repositories == local
            return portfolio

    engine = object.__new__(MissionEngine)
    monkeypatch.setattr(
        "core.autonomy.mission_engine.GitHubRepositoryPortfolio",
        FakePortfolio,
    )
    monkeypatch.setattr(engine, "_discover_workspace_repositories", lambda started: (
        local,
        {"repos_scanned": 1, "repos_skipped": 0, "branches_truncated": 0},
    ))
    monkeypatch.setattr(engine, "_render_repository_output", lambda repositories: "Found repositories: demo")

    result = engine._execute_list_repositories_mission(SimpleNamespace(mission_id="mission-test"))

    assert result["portfolio_inventory"] is portfolio
    assert result["github_count"] == 1
    assert result["comparison"]["default_branch_synced"] == 1
    assert "GitHub portfolio comparison" in result["output"]
    assert "credential_warnings=0" in result["output"]
