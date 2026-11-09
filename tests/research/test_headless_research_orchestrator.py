from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from core.research.headless_research_orchestrator import (
    HeadlessResearchError,
    HeadlessResearchOrchestrator,
)


class FakeBrowser:
    instances = []

    def __init__(self, *, allowed_hosts, headed, timeout_ms):
        self.allowed_hosts = allowed_hosts
        self.headed = headed
        self.timeout_ms = timeout_ms
        self.closed = False
        self.instances.append(self)

    def start(self):
        return {"headless": not self.headed}

    def navigate(self, url):
        self.url = url
        return {"url": url, "title": "Search"}

    def read_page(self, *, max_chars):
        return {"url": self.url, "title": "Search", "text": "Result content", "truncated": False}

    def read_links(self, *, max_links):
        return [
            {"url": "https://github.com/example/lab", "text": "Example Lab"},
            {"url": "https://example.org/docs", "text": "Documentation"},
        ][:max_links]

    def close(self):
        self.closed = True


def test_web_search_runs_headless_and_closes_ephemeral_browser():
    FakeBrowser.instances.clear()
    research = HeadlessResearchOrchestrator(browser_factory=FakeBrowser)
    result = research.search_web("python agent orchestration", limit=2)
    assert result["status"] == "completed"
    assert result["headless"] is True
    assert result["authenticated"] is False
    assert len(result["sources"]) == 2
    browser = FakeBrowser.instances[-1]
    assert browser.headed is False
    assert browser.closed is True


def test_web_search_stops_on_challenge_without_bypass(monkeypatch):
    class ChallengeBrowser(FakeBrowser):
        def read_page(self, *, max_chars):
            return {"title": "Security", "text": "Please verify you are human"}

    result = HeadlessResearchOrchestrator(
        browser_factory=ChallengeBrowser
    ).search_web("python automation")
    assert result["status"] == "blocked_challenge"
    assert result["sources"] == []


def test_github_repository_search_uses_fixed_read_only_argv(monkeypatch):
    calls = []

    def fake_run(argv, **kwargs):
        calls.append((argv, kwargs))
        payload = [{
            "fullName": "example/agent-lab",
            "description": "Research laboratory",
            "url": "https://github.com/example/agent-lab",
            "stargazersCount": 123,
            "forksCount": 10,
            "updatedAt": "2026-11-01T00:00:00Z",
            "pushedAt": "2026-11-02T00:00:00Z",
            "isArchived": False,
            "isFork": False,
            "license": {"name": "MIT"},
            "primaryLanguage": {"name": "Python"},
            "visibility": "PUBLIC",
        }]
        return SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr="")

    monkeypatch.setattr(
        "core.research.headless_research_orchestrator.subprocess.run",
        fake_run,
    )
    research = HeadlessResearchOrchestrator(gh_executable="gh")
    result = research.search_github_repositories("agent research framework", limit=3)
    assert result["status"] == "completed"
    assert result["repositories"][0]["laboratory_decision"] == "not_evaluated"
    argv, kwargs = calls[0]
    assert argv[:4] == ["gh", "search", "repos", "agent research framework"]
    assert "--archived=false" in argv
    assert "--visibility" in argv and "public" in argv
    assert kwargs["shell"] is False
    assert kwargs["stdin"] is __import__("subprocess").DEVNULL
    assert result["mutated_repositories"] is False


def test_github_search_does_not_expose_stderr_or_secrets(monkeypatch):
    def fake_run(argv, **kwargs):
        return SimpleNamespace(returncode=1, stdout="", stderr="GH_TOKEN=secret account=user")

    monkeypatch.setattr(
        "core.research.headless_research_orchestrator.subprocess.run",
        fake_run,
    )
    result = HeadlessResearchOrchestrator(gh_executable="gh").search_github_repositories(
        "agent research framework"
    )
    assert result == {
        "status": "failed",
        "query": "agent research framework",
        "repositories": [],
        "exit_code": 1,
    }
    assert "secret" not in str(result)


@pytest.mark.parametrize("query", ["", "ab", "x" * 301, None])
def test_invalid_query_is_rejected(query):
    with pytest.raises(HeadlessResearchError):
        HeadlessResearchOrchestrator(browser_factory=FakeBrowser).search_web(query)


def test_read_public_url_requires_explicit_allowlist():
    with pytest.raises(HeadlessResearchError):
        HeadlessResearchOrchestrator(browser_factory=FakeBrowser).read_public_url(
            "https://example.org", allowed_hosts=[]
    )
