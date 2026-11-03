"""Read-only inventory of local AI chat sources; never reads browser credentials/content."""
from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote, urlsplit

PROVIDER_HOSTS = {
    "chatgpt": ("chatgpt.com",),
    "grok": ("grok.com",),
    "gemini": ("gemini.google.com", "bard.google.com"),
}
APP_NAMES = ("chatgpt", "grok", "gemini")
INBOX_README = """# DGM-MAT — conversation export intake

Place original provider export archives in the matching folder:

- `chatgpt/`: ChatGPT account export ZIP or conversations JSON.
- `gemini/`: Google Takeout ZIP or TGZ containing Gemini Apps Activity.
- `grok/`: Grok/X account export archive. The exact conversation schema must be validated before import.

Safety:
- Keep the original archive unchanged; DGM-MAT reads a copy/stream and records SHA-256.
- Never place passwords, cookies, API keys, browser profiles or token files here.
- Do not extract archives manually unless an import report explicitly asks for a specific member.
- Unknown formats are inventoried, not silently imported.
- Provider exports may be incomplete and do not restore deleted/private chats.
"""

def _provider_for_host(host: str) -> str | None:
    normalized = host.casefold().rstrip(".")
    for provider, hosts in PROVIDER_HOSTS.items():
        if any(normalized == item or normalized.endswith("." + item) for item in hosts):
            return provider
    return None


def _conversation_id(provider: str, path: str) -> str | None:
    marker = "/app/" if provider == "gemini" else "/c/"
    match = re.search(re.escape(marker) + r"([^/]+)/?$", path, re.IGNORECASE)
    return unquote(match.group(1)) if match else None


def _timestamp(value: Any) -> str | None:
    if not isinstance(value, int) or value <= 0:
        return None
    try:
        return datetime.fromtimestamp(
            value / 1_000_000 - 11_644_473_600, tz=timezone.utc
        ).isoformat()
    except (OverflowError, OSError, ValueError):
        return None


def _history_snapshot(profile: Path, limit: int) -> dict[str, Any]:
    history = profile / "History"
    wal = profile / "History-wal"
    wal_present = wal.is_file() and wal.stat().st_size > 0
    result: dict[str, Any] = {
        "status": "not_found",
        "snapshot_mode": "immutable_main_database",
        "history_db_present": history.is_file(),
        "wal_present": wal_present,
        "wal_bytes": wal.stat().st_size if wal_present else 0,
        "url_rows_by_provider": {name: 0 for name in APP_NAMES},
        "conversation_routes_by_provider": {name: 0 for name in APP_NAMES},
        "conversation_entries": {name: [] for name in APP_NAMES},
        "complete": False,
        "content_read": False,
        "credentials_read": False,
        "note": (
            "Chrome History main database only; uncheckpointed WAL entries are excluded. "
            "Visit metadata is not a complete provider export."
        ),
    }
    if not history.is_file():
        return result

    uri = "file:" + quote(history.as_posix(), safe="/:") + "?mode=ro&immutable=1"
    routes: dict[str, dict[str, dict[str, Any]]] = {name: {} for name in APP_NAMES}
    try:
        connection = sqlite3.connect(uri, uri=True, timeout=0.5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only=ON")
        connection.execute("PRAGMA busy_timeout=500")
        for row in connection.execute(
            "SELECT title, url, last_visit_time, visit_count FROM urls "
            "ORDER BY last_visit_time DESC"
        ):
            parsed = urlsplit(str(row["url"] or ""))
            provider = _provider_for_host(parsed.hostname or "")
            if provider is None:
                continue
            result["url_rows_by_provider"][provider] += 1
            path = parsed.path or "/"
            conversation_id = _conversation_id(provider, path)
            if not conversation_id:
                continue
            # Project-prefixed and direct ChatGPT URLs can identify the same chat.
            # Dedupe by provider conversation ID, not by route spelling.
            route_key = conversation_id
            # The path is retained without query/fragment; no cookies or page bodies.
            entry = {
                "conversation_id": conversation_id[:240],
                "title": str(row["title"] or "")[:200],
                "path": path[:240],
                "last_visit_utc": _timestamp(row["last_visit_time"]),
                "visit_count": max(0, int(row["visit_count"] or 0)),
            }
            existing = routes[provider].get(route_key)
            if existing is None:
                routes[provider][route_key] = entry
            elif (entry["last_visit_utc"] or "") > (existing["last_visit_utc"] or ""):
                routes[provider][route_key] = entry
        connection.close()
        result["status"] = "read_only_snapshot"
        result["conversation_routes_by_provider"] = {
            provider: len(routes[provider]) for provider in APP_NAMES
        }
        for provider in APP_NAMES:
            result["conversation_entries"][provider] = sorted(
                routes[provider].values(),
                key=lambda item: item["last_visit_utc"] or "",
                reverse=True,
            )[:limit]
    except (sqlite3.Error, OSError, ValueError) as exc:
        result["status"] = "locked_or_unavailable"
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)[:240]
    return result


def inventory_local_ai_sources(
    *,
    profile_root: str | Path | None = None,
    shortcuts_dir: str | Path | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """Inventory Chrome PWA indicators and browser visit metadata without page content."""
    if not 1 <= limit <= 500:
        raise ValueError("limit must be between 1 and 500")

    import os

    local = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    roaming = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    profiles = Path(profile_root) if profile_root else local / "Google" / "Chrome" / "User Data"
    shortcuts = Path(shortcuts_dir) if shortcuts_dir else (
        roaming / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Apps do Chrome"
    )

    shortcut_names = (
        sorted(
            path.stem.casefold()
            for path in shortcuts.glob("*.lnk")
            if path.is_file()
        )
        if shortcuts.is_dir()
        else []
    )

    profile_results = []
    if profiles.is_dir():
        for profile in sorted(
            (
                path for path in profiles.iterdir()
                if path.is_dir()
                and ((path / "History").is_file() or (path / "Preferences").is_file())
            ),
            key=lambda path: path.name.casefold(),
        ):
            indexeddb = profile / "IndexedDB"
            origin_names = []
            if indexeddb.is_dir():
                for origin in indexeddb.iterdir():
                    name = origin.name.casefold()
                    if any(host in name for hosts in PROVIDER_HOSTS.values() for host in hosts):
                        origin_names.append(origin.name[:240])
            history = _history_snapshot(profile, limit)
            detected = {}
            for provider, hosts in PROVIDER_HOSTS.items():
                detected[provider] = {
                    "start_menu_shortcut": provider in shortcut_names,
                    "indexeddb_origin_directory_seen": any(
                        any(host in name.casefold() for host in hosts)
                        for name in origin_names
                    ),
                    "history_url_rows": history["url_rows_by_provider"][provider],
                    "history_conversation_routes": history["conversation_routes_by_provider"][provider],
                }
            profile_results.append({
                "profile_name": profile.name,
                "profile_path": str(profile),
                "detected_providers": detected,
                "indexeddb_origin_names_only": sorted(origin_names),
                "history": history,
            })

    return {
        "schema": "dgm-mat-ai-source-inventory.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "local Chrome application indicators and browser history metadata only",
        "providers": list(APP_NAMES),
        "chrome_shortcuts_detected": shortcut_names,
        "profiles": profile_results,
        "conversation_content_read": False,
        "cookies_or_tokens_read": False,
        "provider_accounts_accessed": False,
        "source_data_modified": False,
        "complete_conversation_inventory": False,
        "limitations": [
            "Browser visit titles and routes are metadata, not conversation transcripts.",
            "The immutable History snapshot excludes uncheckpointed History-wal entries.",
            "Private chats, deleted chats, other Chrome profiles and other devices may be absent.",
            "IndexedDB is inspected by directory name only; its contents are never read.",
            "A provider export is required for complete, searchable conversation ingestion.",
        ],
    }


def prepare_recovery_inbox(root: str | Path | None = None) -> dict[str, Any]:
    """Create non-destructive provider intake folders; never overwrite existing files."""
    import os

    base = Path(root) if root else (
        Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        / "DGM-MAT" / "recovery-inbox"
    )
    folders = []
    for provider in (*APP_NAMES, "_unknown"):
        folder = base / provider
        folder.mkdir(parents=True, exist_ok=True)
        folders.append(str(folder))
    readme = base / "README.md"
    created_readme = False
    if not readme.exists():
        readme.write_text(INBOX_README, encoding="utf-8")
        created_readme = True
    return {
        "root": str(base),
        "folders": folders,
        "readme": str(readme),
        "readme_created": created_readme,
    }


def write_inventory_report(report: dict[str, Any], output_path: str | Path) -> Path:
    """Write a local JSON report; callers choose a private diagnostics directory."""
    destination = Path(output_path).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(destination)
    return destination
