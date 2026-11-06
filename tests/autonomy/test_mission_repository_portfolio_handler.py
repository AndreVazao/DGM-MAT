from types import SimpleNamespace

from core.autonomy.mission_engine import MissionEngine


def test_list_repositories_mission_includes_github_portfolio(monkeypatch):
    local = [{"name": "demo", "path": "C:/workspace/demo"}]
    scan = {
        "total_candidates": 1, "current_page": 1, "page_size": 20,
        "page_offset": 0, "next_cursor": None, "has_more": False,
        "complete": True, "partial": False, "repos_scanned": 1,
        "repos_skipped": 0, "repos_previously_paginated": 0,
        "branches_truncated": 0, "root_warnings": [],
    }
    portfolio = {
        "github_api_available": True,
        "summary": {
            "local_repositories": 1, "github_repositories": 1,
            "matched_repositories": 1, "local_only": 0, "github_only": 0,
            "origin_credentials_present": 0, "default_branch_synced": 1,
        },
        "matched": [{"name": "demo", "origin_matches_github": True}],
        "local_only": [], "github_only": [],
    }

    class FakePortfolio:
        def __init__(self, **kwargs):
            assert kwargs["timeout"] == 20
            assert kwargs["roots"]

        def build_inventory(self):
            return portfolio

    engine = object.__new__(MissionEngine)
    monkeypatch.setattr("core.autonomy.mission_engine.GitHubRepositoryPortfolio", FakePortfolio)
    monkeypatch.setattr(
        engine, "_discover_workspace_repositories",
        lambda started, **kwargs: (local, scan),
    )
    monkeypatch.setattr(engine, "_render_repository_output", lambda repositories: "Found repositories: demo")

    result = engine._execute_list_repositories_mission(
        SimpleNamespace(mission_id="mission-test", metadata={}, goal="list repositories")
    )

    assert result["portfolio_inventory"] is portfolio
    assert result["github_count"] == 1
    assert result["comparison"]["default_branch_synced"] == 1
    assert "GitHub portfolio comparison" in result["output"]
    assert "credential_warnings=0" in result["output"]
