"""Headless, read-only web and GitHub research for DGM-MAT.

This module deliberately does not clone repositories, install dependencies, log
into provider accounts, or execute code found on the web. It returns bounded,
source-linked research results for a later reviewed laboratory decision.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass
from typing import Any
from urllib.parse import quote_plus, urlparse

from core.providers.browser.governed_browser_session import GovernedBrowserSession


class HeadlessResearchError(ValueError):
    """A research request is outside the bounded public-research contract."""


@dataclass(frozen=True)
class ResearchSource:
    title: str
    url: str
    snippet: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


class HeadlessResearchOrchestrator:
    """Public web and GitHub research without opening a visible browser window."""

    SEARCH_HOSTS = ("html.duckduckgo.com", "duckduckgo.com")
    GH_FIELDS = (
        "fullName,description,url,stargazersCount,forksCount,updatedAt,"
        "pushedAt,isArchived,isFork,license,primaryLanguage,visibility"
    )
    MAX_QUERY_CHARS = 300
    MAX_RESULTS = 10
    MAX_OUTPUT_BYTES = 512_000
    DEFAULT_TIMEOUT_SECONDS = 25

    def __init__(
        self,
        *,
        browser_factory=GovernedBrowserSession,
        gh_executable: str | None = None,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, int) or not 5 <= timeout_seconds <= 60:
            raise ValueError("timeout_seconds must be an integer between 5 and 60")
        self.browser_factory = browser_factory
        self.gh_executable = gh_executable or shutil.which("gh")
        self.timeout_seconds = timeout_seconds

    @classmethod
    def _validate_query(cls, query: str) -> str:
        if not isinstance(query, str):
            raise HeadlessResearchError("Research query must be text.")
        normalized = " ".join(query.split())
        if not 3 <= len(normalized) <= cls.MAX_QUERY_CHARS:
            raise HeadlessResearchError("Research query must contain 3-300 characters.")
        return normalized

    @classmethod
    def _validate_limit(cls, limit: int) -> int:
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= cls.MAX_RESULTS:
            raise HeadlessResearchError("Result limit must be an integer between 1 and 10.")
        return limit

    @staticmethod
    def _minimal_gh_environment() -> dict[str, str]:
        """Retain only process plumbing and user profile paths used by gh config.

        Credential values are never read, copied into receipts, or returned.
        gh itself uses its normal OS-protected authentication store if present.
        """
        allowed = {
            "PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "TEMP", "TMP",
            "HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA",
        }
        env = {
            key: value for key, value in os.environ.items()
            if key.upper() in allowed and isinstance(value, str)
        }
        env.update({"GH_PROMPT_DISABLED": "1", "GH_PAGER": "cat", "NO_COLOR": "1"})
        return env

    @staticmethod
    def _is_challenge(text: str, title: str) -> bool:
        sample = f"{title}\n{text}".casefold()
        markers = (
            "captcha", "verify you are human", "unusual traffic",
            "automated requests", "security challenge",
        )
        return any(marker in sample for marker in markers)

    def search_web(self, query: str, *, limit: int = 8) -> dict[str, Any]:
        """Search public web results using a headless, ephemeral browser session."""
        normalized = self._validate_query(query)
        result_limit = self._validate_limit(limit)
        session = self.browser_factory(
            allowed_hosts=list(self.SEARCH_HOSTS),
            headed=False,
            timeout_ms=min(self.timeout_seconds * 1000, 30000),
        )
        try:
            session.start()
            search_url = (
                "https://html.duckduckgo.com/html/?q="
                + quote_plus(normalized)
            )
            navigation = session.navigate(search_url)
            page = session.read_page(max_chars=30000)
            title = str(page.get("title") or navigation.get("title") or "")
            body = str(page.get("text") or "")
            if self._is_challenge(body, title):
                return {
                    "status": "blocked_challenge",
                    "query": normalized,
                    "sources": [],
                    "summary_text": "",
                    "message": "The search provider presented a challenge; no bypass was attempted.",
                }
            links = session.read_links(max_links=min(result_limit * 3, 30))
            sources: list[ResearchSource] = []
            seen: set[str] = set()
            for link in links:
                if not isinstance(link, dict):
                    continue
                url = str(link.get("url") or "")
                if not url or url in seen:
                    continue
                parsed = urlparse(url)
                if parsed.scheme != "https" or not parsed.hostname:
                    continue
                if parsed.hostname.casefold() in self.SEARCH_HOSTS:
                    continue
                seen.add(url)
                sources.append(ResearchSource(
                    title=str(link.get("text") or parsed.hostname)[:240],
                    url=url,
                    snippet=str(link.get("snippet") or "")[:500],
                ))
                if len(sources) >= result_limit:
                    break
            return {
                "status": "completed" if sources else "no_results",
                "query": normalized,
                "sources": [source.to_dict() for source in sources],
                "summary_text": body[:12000],
                "source_count": len(sources),
                "headless": True,
                "authenticated": False,
            }
        except Exception as exc:
            return {
                "status": "failed",
                "query": normalized,
                "sources": [],
                "summary_text": "",
                "error_type": type(exc).__name__,
            }
        finally:
            session.close()

    def search_github_repositories(self, query: str, *, limit: int = 10) -> dict[str, Any]:
        """Search public GitHub repositories through the fixed read-only gh command."""
        normalized = self._validate_query(query)
        result_limit = self._validate_limit(limit)
        if not self.gh_executable:
            return {
                "status": "unavailable",
                "query": normalized,
                "repositories": [],
                "message": "GitHub CLI (gh) was not found on PATH.",
            }
        argv = [
            self.gh_executable, "search", "repos", normalized,
            "--limit", str(result_limit),
            "--json", self.GH_FIELDS,
            "--archived=false",
            "--visibility", "public",
        ]
        try:
            completed = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                shell=False,
                timeout=self.timeout_seconds,
                env=self._minimal_gh_environment(),
                stdin=subprocess.DEVNULL,
            )
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "query": normalized, "repositories": []}
        except OSError as exc:
            return {
                "status": "failed",
                "query": normalized,
                "repositories": [],
                "error_type": type(exc).__name__,
            }
        raw = completed.stdout or ""
        if len(raw.encode("utf-8", errors="replace")) > self.MAX_OUTPUT_BYTES:
            return {"status": "rejected_oversized", "query": normalized, "repositories": []}
        if completed.returncode != 0:
            # Do not return stderr: gh may include private host/account details.
            return {
                "status": "failed",
                "query": normalized,
                "repositories": [],
                "exit_code": completed.returncode,
            }
        try:
            decoded = json.loads(raw)
        except json.JSONDecodeError:
            return {"status": "invalid_response", "query": normalized, "repositories": []}
        if not isinstance(decoded, list):
            return {"status": "invalid_response", "query": normalized, "repositories": []}
        repositories = []
        for item in decoded[:result_limit]:
            if not isinstance(item, dict):
                continue
            url = str(item.get("url") or "")
            parsed = urlparse(url)
            if parsed.scheme != "https" or parsed.hostname != "github.com":
                continue
            repositories.append({
                "full_name": str(item.get("fullName") or "")[:200],
                "description": str(item.get("description") or "")[:1000],
                "url": url,
                "stars": item.get("stargazersCount"),
                "forks": item.get("forksCount"),
                "updated_at": item.get("updatedAt"),
                "pushed_at": item.get("pushedAt"),
                "archived": bool(item.get("isArchived")),
                "fork": bool(item.get("isFork")),
                "license": item.get("license"),
                "primary_language": item.get("primaryLanguage"),
                "visibility": item.get("visibility"),
                "laboratory_decision": "not_evaluated",
            })
        return {
            "status": "completed" if repositories else "no_results",
            "query": normalized,
            "repositories": repositories,
            "source_count": len(repositories),
            "mutated_repositories": False,
            "cloned": False,
            "code_executed": False,
        }

    def read_public_url(self, url: str, *, allowed_hosts: list[str]) -> dict[str, Any]:
        """Read one explicitly allowlisted HTTPS page in a headless ephemeral context."""
        if not isinstance(url, str) or len(url) > 2048:
            raise HeadlessResearchError("URL must be text no longer than 2048 characters.")
        parsed = urlparse(url)
        if (
            parsed.scheme != "https" or not parsed.hostname
            or parsed.username or parsed.password
            or not isinstance(allowed_hosts, list) or not allowed_hosts
        ):
            raise HeadlessResearchError("A credential-free HTTPS URL and explicit host allowlist are required.")
        session = self.browser_factory(
            allowed_hosts=allowed_hosts,
            headed=False,
            timeout_ms=min(self.timeout_seconds * 1000, 30000),
        )
        try:
            session.start()
            navigation = session.navigate(url)
            page = session.read_page(max_chars=30000)
            return {
                "status": "completed",
                "url": str(page.get("url") or navigation.get("url") or url),
                "title": str(page.get("title") or "")[:500],
                "text": str(page.get("text") or "")[:30000],
                "truncated": bool(page.get("truncated")),
                "headless": True,
                "authenticated": False,
            }
        finally:
            session.close()
