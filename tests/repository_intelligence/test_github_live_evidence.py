from __future__ import annotations

from core.repository_intelligence import github_live_evidence as live


class _Response:
    def __init__(self, status_code: int, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def test_rejects_non_github_and_noncanonical_origins_without_network(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("network must not be called")

    monkeypatch.setattr(live.requests, "get", fail)
    assert live.fetch_github_live_evidence("gitlab.com/acme/project")["status"] == "unsupported_origin"
    assert live.fetch_github_live_evidence("github.com/acme")["status"] == "unsupported_origin"


def test_fetches_repo_and_checks_for_exact_local_head(monkeypatch):
    live._CACHE.clear()
    calls = []

    def fake_get(url, **kwargs):
        calls.append((url, kwargs))
        if url.endswith("/repos/acme/project"):
            return _Response(200, {
                "full_name": "acme/project",
                "html_url": "https://github.com/acme/project",
                "default_branch": "main",
                "archived": False,
                "visibility": "public",
                "pushed_at": "2026-11-13T10:00:00Z",
                "updated_at": "2026-11-13T10:01:00Z",
            })
        if url.endswith("/pulls"):
            return _Response(200, [{"number": 7, "title": "PR title", "state": "open", "updated_at": "2026-11-13T10:00:00Z", "html_url": "https://github.com/acme/project/pull/7", "draft": True, "labels": [{"name": "enhancement"}]}])
        if url.endswith("/issues"):
            return _Response(200, [{"number": 8, "title": "Issue title", "state": "open", "updated_at": "2026-11-13T10:00:00Z", "html_url": "https://github.com/acme/project/issues/8", "labels": [{"name": "bug"}]}, {"number": 9, "title": "PR duplicate", "pull_request": {"url": "https://api.github.com/pr/9"}}])
        return _Response(200, {
            "total_count": 2,
            "check_runs": [
                {"name": "tests", "status": "completed", "conclusion": "success",
                 "started_at": "2026-11-13T10:00:00Z", "completed_at": "2026-11-13T10:01:00Z",
                 "html_url": "https://github.com/acme/project/actions/runs/1", "app": {"slug": "github-actions"}},
                {"name": "lint", "status": "completed", "conclusion": "failure",
                 "started_at": "2026-11-13T10:00:00Z", "completed_at": "2026-11-13T10:01:00Z",
                 "html_url": "https://github.com/acme/project/actions/runs/2", "app": {"slug": "github-actions"}},
            ],
        })

    monkeypatch.setattr(live.requests, "get", fake_get)
    result = live.fetch_github_live_evidence(
        "https://github.com/acme/project.git",
        "a" * 40,
    )

    assert result["status"] == "available"
    assert result["repository"]["full_name"] == "acme/project"
    assert result["commit_checks"]["commit_sha"] == "a" * 40
    assert result["commit_checks"]["total_count"] == 2
    assert result["commit_checks"]["conclusion_summary"] == {"success": 1, "failure": 1}
    assert len(calls) == 4
    assert result["open_work_items"]["pull_requests"]["items"][0]["number"] == 7
    assert result["open_work_items"]["issues"]["returned"] == 1
    assert all(call[1]["allow_redirects"] is False for call in calls)


def test_repository_metadata_survives_checks_endpoint_failure(monkeypatch):
    live._CACHE.clear()
    calls = 0

    def fake_get(url, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            return _Response(200, {"full_name": "acme/project", "default_branch": "main"})
        return _Response(403, {})

    monkeypatch.setattr(live.requests, "get", fake_get)
    result = live.fetch_github_live_evidence("git@github.com:acme/project.git", "b" * 40)
    assert result["status"] == "partial"
    assert result["repository"]["full_name"] == "acme/project"
    assert result["commit_checks"]["status"] == "unavailable"
    assert result["commit_checks"]["error_type"] == "rate_limited_or_forbidden"


def test_uses_short_cache_for_repeated_dossier_reads(monkeypatch):
    live._CACHE.clear()
    calls = []

    def fake_get(url, **kwargs):
        calls.append(url)
        if url.endswith("/repos/acme/project"):
            return _Response(200, {"full_name": "acme/project", "default_branch": "main"})
        return _Response(200, [])

    monkeypatch.setattr(live.requests, "get", fake_get)
    first = live.fetch_github_live_evidence("github.com/acme/project")
    second = live.fetch_github_live_evidence("github.com/acme/project")
    assert first["status"] == second["status"] == "available"
    assert len(calls) == 3

def test_dossier_calls_live_github_only_after_exact_local_path_match(tmp_path, monkeypatch):
    from core.repository_intelligence import project_dossier as dossier_module
    from core.vault.catalog import VaultCatalog

    repo = tmp_path / "sample-repo"
    repo.mkdir()
    vault = VaultCatalog(vault_root=tmp_path / "vault")
    vault.register_project("sample", "Sample Project", repo)
    calls = []

    def fake_live(origin, commit_sha):
        calls.append((origin, commit_sha))
        return {"status": "available", "observed_at": "2026-11-13T12:00:00Z"}

    monkeypatch.setattr(dossier_module, "fetch_github_live_evidence", fake_live)
    inventory = [{
        "path": str(repo), "origin": "github.com/acme/project",
        "head_sha": "c" * 40, "name": "sample-repo", "branch": "main",
        "dirty": False, "scan_status": "complete", "scan_error": None,
        "last_seen_at": "2026-11-13T11:00:00Z", "scan_count": 1,
    }]

    result = dossier_module.build_project_dossier(
        vault=vault, project_id="sample", repository_inventory=inventory
    )
    assert calls == [("github.com/acme/project", "c" * 40)]
    assert result["repository"]["local_inventory"]["repositories"][0]["github_live"]["status"] == "available"


def test_dossier_does_not_query_github_for_unmatched_local_path(tmp_path, monkeypatch):
    from core.repository_intelligence import project_dossier as dossier_module
    from core.vault.catalog import VaultCatalog

    repo = tmp_path / "sample-repo"
    repo.mkdir()
    vault = VaultCatalog(vault_root=tmp_path / "vault")
    vault.register_project("sample", "Sample Project", repo)

    def fail(*args, **kwargs):
        raise AssertionError("unmatched repository must not trigger a GitHub request")

    monkeypatch.setattr(dossier_module, "fetch_github_live_evidence", fail)
    result = dossier_module.build_project_dossier(
        vault=vault,
        project_id="sample",
        repository_inventory=[{
            "path": str(tmp_path / "different" / "sample-repo"),
            "origin": "github.com/acme/project",
            "head_sha": "d" * 40,
        }],
    )
    assert result["repository"]["local_inventory"]["match_status"] == "no_exact_path_match"

def test_issue_endpoint_excludes_pull_requests_and_limits_returned_fields(monkeypatch):
    live._CACHE.clear()
    def fake_get(url, **kwargs):
        if url.endswith("/repos/acme/project"):
            return _Response(200, {"full_name": "acme/project"})
        if url.endswith("/pulls"):
            return _Response(200, [])
        return _Response(200, [
            {"number": 10, "title": "Real issue", "state": "open", "updated_at": "2026-11-13T10:00:00Z",
             "html_url": "https://github.com/acme/project/issues/10", "body": "must not be copied",
             "labels": [{"name": "bug"}]},
            {"number": 11, "title": "PR mirrored by issues API", "pull_request": {"url": "private"}},
        ])
    monkeypatch.setattr(live.requests, "get", fake_get)
    result = live.fetch_github_live_evidence("https://github.com/acme/project")
    issues = result["open_work_items"]["issues"]["items"]
    assert len(issues) == 1
    assert issues[0]["number"] == 10
    assert "body" not in issues[0]
    assert result["open_work_items"]["pull_requests"]["returned"] == 0


def test_open_work_item_failure_is_partial_not_success(monkeypatch):
    live._CACHE.clear()
    def fake_get(url, **kwargs):
        if url.endswith("/repos/acme/project"):
            return _Response(200, {"full_name": "acme/project"})
        if url.endswith("/pulls"):
            return _Response(403, {})
        return _Response(200, [])
    monkeypatch.setattr(live.requests, "get", fake_get)
    result = live.fetch_github_live_evidence("github.com/acme/project")
    assert result["status"] == "partial"
    assert result["open_work_items"]["pull_requests"]["error_type"] == "rate_limited_or_forbidden"
