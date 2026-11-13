"""Bounded, read-only live GitHub evidence for an exactly identified repository."""
from __future__ import annotations

import os
import re
import threading
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlsplit

import requests


_API = "https://api.github.com"
_TIMEOUT_SECONDS = 5.0
_CACHE_TTL_SECONDS = 300.0
_CACHE_LOCK = threading.Lock()
_CACHE: dict[tuple[str, str, str], tuple[float, dict[str, Any]]] = {}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _github_identity(origin: str) -> tuple[str, str] | None:
    """Accept only a canonical github.com owner/repository origin."""
    value = str(origin or "").strip()
    if not value:
        return None
    if value.startswith("git@"):
        host_path = value[4:].replace(":", "/", 1)
        parsed = urlsplit("https://" + host_path)
    else:
        parsed = urlsplit(value if "://" in value else "https://" + value)
    if (parsed.hostname or "").casefold() != "github.com":
        return None
    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) != 2:
        return None
    owner, repository = parts
    repository = repository.removesuffix(".git")
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", owner):
        return None
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", repository):
        return None
    return owner, repository


def _copy(value: dict[str, Any]) -> dict[str, Any]:
    # The payload contains only JSON-compatible primitive values.
    import json
    return json.loads(json.dumps(value))


def _http_error(response: requests.Response) -> str:
    if response.status_code == 403:
        return "rate_limited_or_forbidden"
    if response.status_code == 404:
        return "not_found_or_private"
    return "github_http_error"


def fetch_github_live_evidence(
    origin: str,
    commit_sha: str | None = None,
    *,
    timeout: float = _TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Read repository metadata and checks for the exact locally observed SHA.

    The function performs at most two GET requests, never follows repository
    redirects, never mutates GitHub, and returns selected metadata only.
    """
    identity = _github_identity(origin)
    if identity is None:
        return {
            "status": "unsupported_origin",
            "source": "github_rest_api_read_only",
            "observed_at": _utc_now(),
            "error_type": "origin_not_canonical_github_repository",
        }

    owner, repository = identity
    sha = str(commit_sha or "").strip().lower()
    if sha and not re.fullmatch(r"[0-9a-f]{40}", sha):
        sha = ""
    cache_key = (f"{owner}/{repository}".casefold(), sha, "authenticated" if os.getenv("GITHUB_TOKEN", "").strip() else "anonymous")
    now_monotonic = time.monotonic()
    with _CACHE_LOCK:
        cached = _CACHE.get(cache_key)
        if cached and now_monotonic - cached[0] < _CACHE_TTL_SECONDS:
            return _copy(cached[1])

    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "DGM-MAT-read-only-project-dossier",
    }
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    observed_at = _utc_now()
    try:
        response = requests.get(
            f"{_API}/repos/{owner}/{repository}",
            headers=headers,
            timeout=max(1.0, min(float(timeout), 10.0)),
            allow_redirects=False,
        )
    except requests.RequestException as exc:
        return {
            "status": "unavailable",
            "source": "github_rest_api_read_only",
            "observed_at": observed_at,
            "error_type": type(exc).__name__,
        }

    if response.status_code != 200:
        return {
            "status": "unavailable",
            "source": "github_rest_api_read_only",
            "observed_at": observed_at,
            "http_status": response.status_code,
            "error_type": _http_error(response),
        }
    try:
        payload = response.json()
    except (TypeError, ValueError):
        return {
            "status": "unavailable",
            "source": "github_rest_api_read_only",
            "observed_at": observed_at,
            "http_status": response.status_code,
            "error_type": "invalid_github_json",
        }
    if not isinstance(payload, dict):
        return {
            "status": "unavailable",
            "source": "github_rest_api_read_only",
            "observed_at": observed_at,
            "http_status": response.status_code,
            "error_type": "invalid_github_payload",
        }

    result: dict[str, Any] = {
        "status": "available",
        "source": "github_rest_api_read_only",
        "observed_at": observed_at,
        "repository": {
            "full_name": payload.get("full_name"),
            "html_url": payload.get("html_url"),
            "default_branch": payload.get("default_branch"),
            "archived": payload.get("archived"),
            "visibility": payload.get("visibility"),
            "pushed_at": payload.get("pushed_at"),
            "updated_at": payload.get("updated_at"),
        },
        "commit_checks": {
            "status": "not_requested_no_exact_local_head",
            "commit_sha": None,
            "total_count": 0,
            "conclusion_summary": {},
            "checks": [],
        },
        "limitations": [
            "GitHub metadata is live at observed_at; local working-tree state remains a separate persisted observation.",
            "Commit checks refer only to the exact local HEAD SHA supplied by repository inventory.",
            "A missing check run is not proof that tests passed.",
        ],
    }

    if sha:
        result["commit_checks"]["commit_sha"] = sha
        try:
            checks_response = requests.get(
                f"{_API}/repos/{owner}/{repository}/commits/{sha}/check-runs",
                headers=headers,
                params={"per_page": 20},
                timeout=max(1.0, min(float(timeout), 10.0)),
                allow_redirects=False,
            )
        except requests.RequestException as exc:
            result["status"] = "partial"
            result["commit_checks"]["status"] = "unavailable"
            result["commit_checks"]["error_type"] = type(exc).__name__
        else:
            if checks_response.status_code != 200:
                result["status"] = "partial"
                result["commit_checks"]["status"] = "unavailable"
                result["commit_checks"]["http_status"] = checks_response.status_code
                result["commit_checks"]["error_type"] = _http_error(checks_response)
            else:
                try:
                    checks_payload = checks_response.json()
                except (TypeError, ValueError):
                    checks_payload = None
                if not isinstance(checks_payload, dict) or not isinstance(checks_payload.get("check_runs"), list):
                    result["status"] = "partial"
                    result["commit_checks"]["status"] = "unavailable"
                    result["commit_checks"]["error_type"] = "invalid_github_checks_payload"
                else:
                    checks = []
                    conclusions: dict[str, int] = {}
                    for item in checks_payload["check_runs"][:20]:
                        if not isinstance(item, dict):
                            continue
                        conclusion = item.get("conclusion")
                        label = str(conclusion or item.get("status") or "unknown")
                        conclusions[label] = conclusions.get(label, 0) + 1
                        checks.append({
                            "name": item.get("name"),
                            "status": item.get("status"),
                            "conclusion": conclusion,
                            "started_at": item.get("started_at"),
                            "completed_at": item.get("completed_at"),
                            "html_url": item.get("html_url"),
                            "app": (item.get("app") or {}).get("slug") if isinstance(item.get("app"), dict) else None,
                        })
                    total_raw = checks_payload.get("total_count")
                    total_count = total_raw if isinstance(total_raw, int) and total_raw >= 0 else len(checks)
                    result["commit_checks"] = {
                        "status": "available",
                        "commit_sha": sha,
                        "total_count": total_count,
                        "returned": len(checks),
                        "truncated": total_count > len(checks),
                        "conclusion_summary": conclusions,
                        "checks": checks,
                    }

    def fetch_recent_records(endpoint: str, *, kind: str) -> dict[str, Any]:
        try:
            collection_response = requests.get(
                f"{_API}/repos/{owner}/{repository}/{endpoint}",
                headers=headers,
                params={"state": "all", "sort": "updated", "direction": "desc", "per_page": 20 if kind == "issue" else 10},
                timeout=max(1.0, min(float(timeout), 10.0)),
                allow_redirects=False,
            )
        except requests.RequestException as exc:
            return {"status": "unavailable", "error_type": type(exc).__name__, "items": []}
        if collection_response.status_code != 200:
            return {
                "status": "unavailable",
                "http_status": collection_response.status_code,
                "error_type": _http_error(collection_response),
                "items": [],
            }
        try:
            collection_payload = collection_response.json()
        except (TypeError, ValueError):
            collection_payload = None
        if not isinstance(collection_payload, list):
            return {"status": "unavailable", "error_type": "invalid_github_collection_payload", "items": []}

        records = []
        for item in collection_payload[:20]:
            if len(records) >= 10:
                break
            if not isinstance(item, dict):
                continue
            is_pull_request = isinstance(item.get("pull_request"), dict)
            if kind == "issue" and is_pull_request:
                continue
            if kind == "pull_request" and not is_pull_request:
                continue
            labels = item.get("labels") if isinstance(item.get("labels"), list) else []
            records.append({
                "number": item.get("number") if isinstance(item.get("number"), int) else None,
                "title": str(item.get("title") or "")[:240],
                "state": item.get("state") if item.get("state") in {"open", "closed"} else "unknown",
                "draft": item.get("draft") if kind == "pull_request" and isinstance(item.get("draft"), bool) else None,
                "created_at": item.get("created_at"),
                "updated_at": item.get("updated_at"),
                "closed_at": item.get("closed_at"),
                "html_url": item.get("html_url"),
                "labels": [
                    str(label.get("name") or "")[:80]
                    for label in labels[:10] if isinstance(label, dict) and label.get("name")
                ],
            })
        return {"status": "available", "returned": len(records), "items": records}

    pull_requests = fetch_recent_records("pulls", kind="pull_request")
    issues = fetch_recent_records("issues", kind="issue")
    result["github_activity"] = {
        "status": "available" if pull_requests["status"] == issues["status"] == "available" else "partial",
        "observed_at": _utc_now(),
        "pull_requests": pull_requests,
        "issues": issues,
        "limitations": [
            "Only the ten most recently updated records per collection are returned.",
            "Issue results exclude pull requests; pull requests are reported separately.",
            "Closed issues and pull requests are historical records, not evidence of current defects or unfinished work.",
        ],
    }
    if result["github_activity"]["status"] != "available" and result["status"] == "available":
        result["status"] = "partial"

    with _CACHE_LOCK:
        _CACHE[cache_key] = (time.monotonic(), _copy(result))
        # Keep this process-local cache bounded.
        if len(_CACHE) > 100:
            oldest = sorted(_CACHE, key=lambda key: _CACHE[key][0])[: len(_CACHE) - 100]
            for key in oldest:
                _CACHE.pop(key, None)
    return result
