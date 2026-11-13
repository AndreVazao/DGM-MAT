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
    assert len(calls) == 2
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
        return _Response(200, {"full_name": "acme/project", "default_branch": "main"})

    monkeypatch.setattr(live.requests, "get", fake_get)
    first = live.fetch_github_live_evidence("github.com/acme/project")
    second = live.fetch_github_live_evidence("github.com/acme/project")
    assert first["status"] == second["status"] == "available"
    assert len(calls) == 1
