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
        if url.endswith("/pulls") or url.endswith("/issues"):
            return _Response(200, [])
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
    assert len(calls) == 6
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
        if url.endswith("/pulls") or url.endswith("/issues"):
            return _Response(200, [])
        return _Response(200, {"full_name": "acme/project", "default_branch": "main"})

    monkeypatch.setattr(live.requests, "get", fake_get)
    first = live.fetch_github_live_evidence("github.com/acme/project")
    second = live.fetch_github_live_evidence("github.com/acme/project")
    assert first["status"] == second["status"] == "available"
    assert len(calls) == 5

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

def test_includes_bounded_pr_and_issue_history_without_mixing_records(monkeypatch):
    live._CACHE.clear()
    calls = []

    def fake_get(url, **kwargs):
        calls.append((url, kwargs))
        if url.endswith("/repos/acme/project"):
            return _Response(200, {"full_name": "acme/project", "default_branch": "main"})
        if url.endswith("/check-runs"):
            return _Response(200, {"total_count": 0, "check_runs": []})
        if url.endswith("/pulls"):
            history = [{
                "number": 12, "title": "Fix mission recovery", "state": "closed",
                "draft": False, "created_at": "2026-11-01T10:00:00Z",
                "updated_at": "2026-11-12T10:00:00Z", "closed_at": "2026-11-12T10:01:00Z",
                "html_url": "https://github.com/acme/project/pull/12",
                "labels": [{"name": "bug"}],
            }, {
                "number": 13, "title": "Open PR without issue marker", "state": "open",
                "draft": True, "created_at": "2026-11-13T10:00:00Z",
                "updated_at": "2026-11-14T10:00:00Z", "closed_at": None,
                "html_url": "https://github.com/acme/project/pull/13", "labels": [],
            }]
            return _Response(200, [item for item in history if kwargs["params"]["state"] == "all" or item["state"] == "open"])
        if url.endswith("/issues"):
            history = [
                {"number": 20, "title": "Track recovery gap", "state": "open",
                 "created_at": "2026-11-02T10:00:00Z", "updated_at": "2026-11-13T10:00:00Z",
                 "closed_at": None, "html_url": "https://github.com/acme/project/issues/20",
                 "labels": [{"name": "recovery"}]},
                {"number": 12, "title": "Fix mission recovery", "state": "closed",
                 "created_at": "2026-11-01T10:00:00Z", "updated_at": "2026-11-12T10:00:00Z",
                 "closed_at": "2026-11-12T10:01:00Z", "html_url": "https://github.com/acme/project/pull/12",
                 "labels": [], "pull_request": {"url": "api"}},
            ]
            return _Response(200, [item for item in history if kwargs["params"]["state"] == "all" or item["state"] == "open"])
        raise AssertionError(url)

    monkeypatch.setattr(live.requests, "get", fake_get)
    result = live.fetch_github_live_evidence("github.com/acme/project", "a" * 40)

    assert result["github_activity"]["status"] == "available"
    assert result["github_activity"]["pull_requests"]["returned"] == 2
    assert result["github_activity"]["pull_requests"]["items"][0]["number"] == 12
    assert result["open_work_items"]["pull_requests"]["returned"] == 1
    assert result["open_work_items"]["pull_requests"]["items"][0]["number"] == 13
    assert result["open_work_items"]["issues"]["items"][0]["number"] == 20
    assert result["github_activity"]["issues"]["returned"] == 1
    assert result["github_activity"]["issues"]["items"][0]["number"] == 20
    assert all(call[1]["params"]["state"] == "all" for call in calls[2:4])
    assert all(call[1]["params"]["state"] == "open" for call in calls[4:6])
    assert calls[2][1]["params"]["per_page"] == 100
    assert calls[3][1]["params"]["per_page"] == 100
    assert calls[4][1]["params"]["per_page"] == 11
    assert calls[5][1]["params"]["per_page"] == 100
    assert len(calls) == 6


def test_github_activity_failure_is_partial_and_preserves_repository_evidence(monkeypatch):
    live._CACHE.clear()
    calls = 0

    def fake_get(url, **kwargs):
        nonlocal calls
        calls += 1
        if url.endswith("/repos/acme/project"):
            return _Response(200, {"full_name": "acme/project", "default_branch": "main"})
        if url.endswith("/pulls"):
            return _Response(200, [])
        if url.endswith("/issues"):
            return _Response(403, {})
        raise AssertionError(url)

    monkeypatch.setattr(live.requests, "get", fake_get)
    result = live.fetch_github_live_evidence("github.com/acme/project")

    assert result["status"] == "partial"
    assert result["repository"]["full_name"] == "acme/project"
    assert result["github_activity"]["status"] == "partial"
    assert result["github_activity"]["issues"]["error_type"] == "rate_limited_or_forbidden"
    assert result["github_activity"]["pull_requests"]["status"] == "available"
    assert result["open_work_items"]["status"] == "partial"
    assert result["open_work_items"]["issues"]["status"] == "unavailable"
    assert calls == 5


def test_history_and_open_work_report_output_limit_truncation_independently(monkeypatch):
    live._CACHE.clear()

    def make_record(number, state):
        return {
            "number": number,
            "title": f"Record {number}",
            "state": state,
            "created_at": "2026-11-14T10:00:00Z",
            "updated_at": "2026-11-14T11:00:00Z",
            "closed_at": None if state == "open" else "2026-11-14T12:00:00Z",
            "html_url": f"https://github.com/acme/project/issues/{number}",
            "labels": [],
        }

    def fake_get(url, **kwargs):
        if url.endswith("/repos/acme/project"):
            return _Response(200, {"full_name": "acme/project", "default_branch": "main"})
        if url.endswith("/pulls"):
            if kwargs["params"]["state"] == "open":
                return _Response(200, [make_record(11, "open")])
            # Eleven history records, but only one open work item.
            return _Response(200, [make_record(i, "closed") for i in range(1, 11)] + [make_record(11, "open")])
        if url.endswith("/issues"):
            # Eleven eligible open issues exceed the separate ten-item open limit.
            return _Response(200, [make_record(i, "open") for i in range(20, 31)])
        raise AssertionError(url)

    monkeypatch.setattr(live.requests, "get", fake_get)
    result = live.fetch_github_live_evidence("github.com/acme/project")

    pr_history = result["github_activity"]["pull_requests"]
    pr_open = result["open_work_items"]["pull_requests"]
    issue_history = result["github_activity"]["issues"]
    issue_open = result["open_work_items"]["issues"]

    assert pr_history["returned"] == 10
    assert pr_history["may_be_truncated"] is True
    assert pr_open["returned"] == 1
    assert pr_open["may_be_truncated"] is False
    assert issue_history["returned"] == 10
    assert issue_history["may_be_truncated"] is True
    assert issue_open["returned"] == 10
    assert issue_open["may_be_truncated"] is True


def test_full_upstream_page_marks_both_projections_as_potentially_truncated(monkeypatch):
    live._CACHE.clear()

    def fake_get(url, **kwargs):
        if url.endswith("/repos/acme/project"):
            return _Response(200, {"full_name": "acme/project", "default_branch": "main"})
        if url.endswith("/pulls"):
            if kwargs["params"]["state"] == "open":
                return _Response(200, [{
                    "number": 101, "title": "Open PR outside recent history page",
                    "state": "open", "draft": False,
                    "created_at": "2026-11-01T10:00:00Z",
                    "updated_at": "2026-11-14T12:00:00Z", "closed_at": None,
                    "html_url": "https://github.com/acme/project/pull/101", "labels": [],
                }])
            return _Response(200, [{
                "number": number,
                "title": f"Closed PR {number}",
                "state": "closed",
                "draft": False,
                "created_at": "2026-11-01T10:00:00Z",
                "updated_at": "2026-11-14T10:00:00Z",
                "closed_at": "2026-11-14T11:00:00Z",
                "html_url": f"https://github.com/acme/project/pull/{number}",
                "labels": [],
            } for number in range(1, 101)])
        if url.endswith("/issues"):
            return _Response(200, [])
        raise AssertionError(url)

    monkeypatch.setattr(live.requests, "get", fake_get)
    result = live.fetch_github_live_evidence("github.com/acme/project")

    assert result["github_activity"]["pull_requests"]["may_be_truncated"] is True
    assert result["open_work_items"]["pull_requests"]["returned"] == 1
    assert result["open_work_items"]["pull_requests"]["items"][0]["number"] == 101
    assert result["open_work_items"]["pull_requests"]["may_be_truncated"] is False
