"""Persistent, incremental repository learning for the DGM-MAT runtime.

The worker inventories repository metadata and a short redacted README summary.
It never edits repositories, changes Git state, runs project code, or follows
symlinked directories. A SQLite ledger makes progress resumable across restarts.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import subprocess
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
from uuid import uuid4

from core.storage.storage_manager import storage_manager


DEFAULT_ROOTS = (
    Path("C:/ProgramasGodMode"),
    Path("C:/DevopGodMode"),
    Path("C:/AI"),
    Path("C:/Projects"),
    Path("C:/ProjectFlux"),
    Path("C:/ProjectMind"),
)
SKIP_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__", "build", "dist",
    "target", ".tox", ".pytest_cache", ".mypy_cache", ".ruff_cache", "vendor",
    ".gradle", ".idea", ".vs", "bin", "obj", "Pods", "Carthage",
}
MANIFESTS = (
    "pyproject.toml", "setup.py", "requirements.txt", "Pipfile",
    "package.json", "Cargo.toml", "go.mod", "composer.json", "pom.xml",
    "build.gradle", "build.gradle.kts", "CMakeLists.txt", "platformio.ini",
    "*.csproj", "*.sln", "*.kicad_pro", "*.ino",
)
_SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|access[_-]?token|refresh[_-]?token|password|passwd|secret)\s*[:=]\s*[^\s,;]{6,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/-]{20,}"),
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _redact(value: str, limit: int = 800) -> str:
    text = value
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text[:limit]


def _safe_origin(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    if "://" in value:
        parsed = urlsplit(value)
        host = parsed.hostname or ""
        path = parsed.path or ""
    elif "@" in value and ":" in value.split("@", 1)[-1]:
        host, path = value.split("@", 1)[1].split(":", 1)
    else:
        return _redact(value, 240)
    return _redact(f"{host}/{path.lstrip('/').removesuffix('.git')}", 240)


class RepositoryLearningService:
    """Incrementally inventory repositories and skip unchanged snapshots."""

    def __init__(
        self,
        *,
        storage_dir: str | Path | None = None,
        roots: list[str | Path] | tuple[str | Path, ...] | None = None,
        batch_size: int = 5,
        max_depth: int = 5,
        refresh_seconds: int = 900,
        command_timeout: float = 4.0,
    ) -> None:
        base = Path(storage_dir) if storage_dir else storage_manager.get_path("cognition") / "repository_learning"
        base.mkdir(parents=True, exist_ok=True)
        self.database_path = base / "repository_learning.sqlite3"
        configured = os.getenv("DGM_REPO_SCAN_ROOTS", "")
        selected = list(roots) if roots is not None else list(DEFAULT_ROOTS)
        if roots is None:
            selected.extend(Path(item.strip()) for item in configured.split(";") if item.strip())
        unique: dict[str, Path] = {}
        for item in selected:
            path = Path(item).expanduser()
            try:
                resolved = path.resolve()
            except (OSError, RuntimeError):
                resolved = path.absolute()
            unique.setdefault(os.path.normcase(str(resolved)).casefold(), resolved)
        self.roots = tuple(sorted(unique.values(), key=lambda item: str(item).casefold()))
        batch_size = int(os.getenv("DGM_REPOSITORY_LEARNING_BATCH_SIZE", batch_size))
        max_depth = int(os.getenv("DGM_REPOSITORY_LEARNING_MAX_DEPTH", max_depth))
        refresh_seconds = int(os.getenv("DGM_REPOSITORY_LEARNING_REFRESH_SECONDS", refresh_seconds))
        self.batch_size = max(1, min(int(batch_size), 25))
        self.max_depth = max(1, min(int(max_depth), 8))
        self.refresh_seconds = max(60, min(int(refresh_seconds), 86400))
        self.command_timeout = max(1.0, min(float(command_timeout), 10.0))
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._initialize()

    def _connection(self) -> sqlite3.Connection:
        db = sqlite3.connect(str(self.database_path), timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=10000")
        db.execute("PRAGMA journal_mode=WAL")
        return db

    def _initialize(self) -> None:
        with self._connection() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS learning_state (
                    state_key TEXT PRIMARY KEY,
                    value_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS repositories (
                    path TEXT PRIMARY KEY,
                    root TEXT NOT NULL,
                    name TEXT NOT NULL,
                    branch TEXT NOT NULL,
                    head_sha TEXT NOT NULL,
                    dirty INTEGER NOT NULL,
                    origin TEXT NOT NULL,
                    protected INTEGER NOT NULL,
                    stack_json TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    fingerprint TEXT NOT NULL,
                    scan_status TEXT NOT NULL,
                    scan_error TEXT,
                    first_seen_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL,
                    last_changed_at TEXT NOT NULL,
                    scan_count INTEGER NOT NULL DEFAULT 1
                );
                CREATE INDEX IF NOT EXISTS ix_repository_learning_root
                    ON repositories(root, name);
                CREATE INDEX IF NOT EXISTS ix_repository_learning_status
                    ON repositories(scan_status, protected);
                CREATE TABLE IF NOT EXISTS learning_runs (
                    run_id TEXT PRIMARY KEY,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    status TEXT NOT NULL,
                    total_candidates INTEGER NOT NULL DEFAULT 0,
                    inspected INTEGER NOT NULL DEFAULT 0,
                    unchanged INTEGER NOT NULL DEFAULT 0,
                    errors INTEGER NOT NULL DEFAULT 0,
                    last_path TEXT
                );
            """)
            db.commit()

    def _read_state(self, db: sqlite3.Connection) -> dict[str, Any]:
        row = db.execute(
            "SELECT value_json FROM learning_state WHERE state_key='active'"
        ).fetchone()
        if not row:
            return {}
        try:
            value = json.loads(row["value_json"])
        except (TypeError, json.JSONDecodeError):
            return {}
        return value if isinstance(value, dict) else {}

    def _write_state(self, db: sqlite3.Connection, state: dict[str, Any]) -> None:
        db.execute("""
            INSERT INTO learning_state(state_key, value_json, updated_at)
            VALUES ('active', ?, ?)
            ON CONFLICT(state_key) DO UPDATE SET
                value_json=excluded.value_json, updated_at=excluded.updated_at
        """, (json.dumps(state, ensure_ascii=False), _now()))

    def _discover_candidates(self) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
        found: dict[str, dict[str, str]] = {}
        warnings: list[dict[str, str]] = []
        for root in self.roots:
            if not root.exists():
                warnings.append({"root": str(root), "status": "missing"})
                continue
            if not root.is_dir():
                warnings.append({"root": str(root), "status": "not_directory"})
                continue
            try:
                if (root / ".git").exists():
                    found[str(root).casefold()] = {"path": str(root), "root": str(root)}
                    continue
                for current, directories, _files in os.walk(root, topdown=True, followlinks=False):
                    current_path = Path(current)
                    depth = len(current_path.relative_to(root).parts)
                    directories[:] = sorted(
                        name for name in directories
                        if name.casefold() not in SKIP_DIRS and not name.startswith(".")
                    )
                    if depth >= self.max_depth:
                        directories[:] = []
                    if (current_path / ".git").exists():
                        key = os.path.normcase(str(current_path.resolve())).casefold()
                        found.setdefault(key, {"path": str(current_path.resolve()), "root": str(root)})
                        directories[:] = []
            except (OSError, PermissionError) as exc:
                warnings.append({"root": str(root), "status": type(exc).__name__})
        candidates = sorted(found.values(), key=lambda item: item["path"].casefold())
        return candidates, warnings

    def _git(self, path: Path, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(path), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=self.command_timeout,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"git_{args[0].replace('-', '_')}_failed")
        return result.stdout.strip()

    @staticmethod
    def _is_protected(path: Path) -> bool:
        return any("DGM-MAT-FULL-MIRROR" in part.upper() for part in path.parts)

    @staticmethod
    def _manifest_stack(path: Path) -> list[str]:
        stack: list[str] = []
        for pattern in MANIFESTS:
            if any(path.glob(pattern)):
                stack.append(pattern)
        return stack

    def _read_project_summary(self, path: Path, protected: bool) -> str:
        if protected:
            return "Protected mirror: metadata inventory only; no project files were read."
        readme = next(
            (path / name for name in ("README.md", "README.rst", "README.txt", "readme.md") if (path / name).is_file()),
            None,
        )
        if readme is None:
            return "No top-level README found."
        try:
            raw = readme.read_text(encoding="utf-8", errors="replace")[:32000]
        except OSError:
            return "README could not be read."
        lines = []
        for line in raw.splitlines():
            cleaned = line.strip()
            if not cleaned or cleaned.startswith("![") or cleaned.startswith("[!["):
                continue
            if cleaned.startswith("#"):
                cleaned = cleaned.lstrip("#").strip()
            if cleaned:
                lines.append(cleaned)
            if len(" ".join(lines)) >= 800:
                break
        return _redact(" ".join(lines), 800) or "README contains no summary text."

    def _inspect(self, item: dict[str, str]) -> dict[str, Any]:
        path = Path(item["path"])
        protected = self._is_protected(path)
        branch = self._git(path, "branch", "--show-current") or "detached"
        head = self._git(path, "rev-parse", "--short=12", "HEAD") or "unknown"
        dirty = bool(self._git(path, "status", "--porcelain=v1", "-uno"))
        try:
            origin = _safe_origin(self._git(path, "remote", "get-url", "origin"))
        except (RuntimeError, subprocess.TimeoutExpired):
            origin = ""
        stack = self._manifest_stack(path)
        summary = self._read_project_summary(path, protected)
        marker_times = []
        for name in ("README.md", "README.rst", "README.txt", "readme.md", *MANIFESTS):
            for marker in path.glob(name):
                try:
                    marker_times.append((marker.name, marker.stat().st_mtime_ns))
                except OSError:
                    pass
        fingerprint_source = json.dumps(
            [head, branch, dirty, origin, stack, sorted(marker_times)],
            ensure_ascii=False,
            separators=(",", ":"),
        )
        fingerprint = hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest()
        return {
            "path": str(path),
            "root": item["root"],
            "name": path.name,
            "branch": branch,
            "head_sha": head,
            "dirty": dirty,
            "origin": origin,
            "protected": protected,
            "stack": stack,
            "summary": summary,
            "fingerprint": fingerprint,
            "scan_status": "protected_metadata_only" if protected else "learned",
            "scan_error": None,
        }


    def run_batch(self, limit: int | None = None) -> dict[str, Any]:
        """Inspect the next bounded page, persisting each result before advancing."""
        batch_size = max(1, min(int(limit or self.batch_size), 25))
        with self._lock, self._connection() as db:
            state = self._read_state(db)
            now = datetime.now(timezone.utc)
            refresh_at = state.get("next_refresh_at")
            refresh_due = True
            if isinstance(refresh_at, str):
                try:
                    refresh_due = now >= datetime.fromisoformat(refresh_at)
                except ValueError:
                    refresh_due = True

            candidates = state.get("candidate_paths")
            cursor = state.get("cursor_index", 0)
            cycle_active = state.get("status") == "running" and isinstance(candidates, list)
            if not cycle_active and not refresh_due and state:
                return self._status_from_db(db, state)

            if not cycle_active:
                discovered, warnings = self._discover_candidates()
                run_id = uuid4().hex
                state = {
                    "run_id": run_id,
                    "status": "running",
                    "started_at": _now(),
                    "candidate_paths": discovered,
                    "cursor_index": 0,
                    "total_candidates": len(discovered),
                    "root_warnings": warnings,
                    "inspected_this_cycle": 0,
                    "unchanged_this_cycle": 0,
                    "errors_this_cycle": 0,
                    "last_path": None,
                    "next_refresh_at": None,
                }
                db.execute("""
                    INSERT INTO learning_runs(run_id, started_at, status, total_candidates)
                    VALUES (?, ?, 'running', ?)
                """, (run_id, state["started_at"], len(discovered)))
                self._write_state(db, state)
                db.commit()
                candidates = discovered
                cursor = 0

            total = len(candidates)
            end = min(total, int(cursor) + batch_size)
            processed = 0
            for index in range(int(cursor), end):
                item = candidates[index]
                path_text = item.get("path", "") if isinstance(item, dict) else str(item)
                if not path_text:
                    state["errors_this_cycle"] = int(state.get("errors_this_cycle", 0)) + 1
                    state["cursor_index"] = index + 1
                    continue
                try:
                    inspected = self._inspect(item if isinstance(item, dict) else {"path": path_text, "root": str(Path(path_text).parent)})
                    previous = db.execute(
                        "SELECT fingerprint, first_seen_at, scan_count FROM repositories WHERE path=?",
                        (inspected["path"],),
                    ).fetchone()
                    unchanged = bool(previous and previous["fingerprint"] == inspected["fingerprint"])
                    timestamp = _now()
                    if unchanged:
                        db.execute(
                            "UPDATE repositories SET last_seen_at=? WHERE path=?",
                            (timestamp, inspected["path"]),
                        )
                        state["unchanged_this_cycle"] = int(state.get("unchanged_this_cycle", 0)) + 1
                    else:
                        first_seen = previous["first_seen_at"] if previous else timestamp
                        scan_count = int(previous["scan_count"]) + 1 if previous else 1
                        db.execute("""
                            INSERT INTO repositories(
                                path, root, name, branch, head_sha, dirty, origin, protected,
                                stack_json, summary, fingerprint, scan_status, scan_error,
                                first_seen_at, last_seen_at, last_changed_at, scan_count
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(path) DO UPDATE SET
                                root=excluded.root, name=excluded.name, branch=excluded.branch,
                                head_sha=excluded.head_sha, dirty=excluded.dirty, origin=excluded.origin,
                                protected=excluded.protected, stack_json=excluded.stack_json,
                                summary=excluded.summary, fingerprint=excluded.fingerprint,
                                scan_status=excluded.scan_status, scan_error=excluded.scan_error,
                                last_seen_at=excluded.last_seen_at, last_changed_at=excluded.last_changed_at,
                                scan_count=excluded.scan_count
                        """, (
                            inspected["path"], inspected["root"], inspected["name"],
                            inspected["branch"], inspected["head_sha"], int(inspected["dirty"]),
                            inspected["origin"], int(inspected["protected"]),
                            json.dumps(inspected["stack"], ensure_ascii=False),
                            inspected["summary"], inspected["fingerprint"], inspected["scan_status"],
                            inspected["scan_error"], first_seen, timestamp, timestamp, scan_count,
                        ))
                        state["inspected_this_cycle"] = int(state.get("inspected_this_cycle", 0)) + 1
                    state["last_path"] = inspected["path"]
                except (OSError, RuntimeError, subprocess.SubprocessError, ValueError) as exc:
                    timestamp = _now()
                    db.execute("""
                        INSERT INTO repositories(
                            path, root, name, branch, head_sha, dirty, origin, protected,
                            stack_json, summary, fingerprint, scan_status, scan_error,
                            first_seen_at, last_seen_at, last_changed_at, scan_count
                        ) VALUES (?, ?, ?, '', '', 0, '', 0, '[]', '', '', 'error', ?, ?, ?, ?, 1)
                        ON CONFLICT(path) DO UPDATE SET
                            scan_status='error', scan_error=excluded.scan_error,
                            last_seen_at=excluded.last_seen_at
                    """, (
                        path_text, item.get("root", str(Path(path_text).parent)) if isinstance(item, dict) else str(Path(path_text).parent),
                        Path(path_text).name, type(exc).__name__, timestamp, timestamp, timestamp,
                    ))
                    state["errors_this_cycle"] = int(state.get("errors_this_cycle", 0)) + 1
                    state["last_path"] = path_text
                state["cursor_index"] = index + 1
                processed += 1
                self._write_state(db, state)
                db.commit()

            complete = int(state.get("cursor_index", 0)) >= total
            if complete:
                completed_at = _now()
                state["status"] = "complete"
                state["completed_at"] = completed_at
                state["next_refresh_at"] = (
                    datetime.now(timezone.utc) + timedelta(seconds=self.refresh_seconds)
                ).isoformat()
                db.execute("""
                    UPDATE learning_runs SET completed_at=?, status='complete',
                        inspected=?, unchanged=?, errors=?, last_path=?
                    WHERE run_id=?
                """, (
                    completed_at, state.get("inspected_this_cycle", 0),
                    state.get("unchanged_this_cycle", 0), state.get("errors_this_cycle", 0),
                    state.get("last_path"), state.get("run_id"),
                ))
                self._write_state(db, state)
                db.commit()
            return self._status_from_db(db, state, processed=processed, cycle_complete=complete)

    def _status_from_db(
        self,
        db: sqlite3.Connection,
        state: dict[str, Any],
        *,
        processed: int = 0,
        cycle_complete: bool | None = None,
    ) -> dict[str, Any]:
        total = int(state.get("total_candidates", 0))
        cursor = int(state.get("cursor_index", 0))
        row = db.execute("""
            SELECT COUNT(*) AS total,
                   SUM(CASE WHEN scan_status='error' THEN 1 ELSE 0 END) AS errors,
                   SUM(CASE WHEN protected=1 THEN 1 ELSE 0 END) AS protected,
                   SUM(CASE WHEN dirty=1 THEN 1 ELSE 0 END) AS dirty
            FROM repositories
        """).fetchone()
        complete = state.get("status") == "complete" if cycle_complete is None else cycle_complete
        return {
            "status": state.get("status", "not_started"),
            "run_id": state.get("run_id"),
            "total_candidates": total,
            "processed_candidates": min(cursor, total),
            "pending_candidates": max(0, total - cursor),
            "repositories_learned": int(row["total"] or 0),
            "repositories_with_errors": int(row["errors"] or 0),
            "protected_repositories": int(row["protected"] or 0),
            "repositories_with_tracked_changes": int(row["dirty"] or 0),
            "inspected_this_cycle": int(state.get("inspected_this_cycle", 0)),
            "unchanged_skipped_this_cycle": int(state.get("unchanged_this_cycle", 0)),
            "errors_this_cycle": int(state.get("errors_this_cycle", 0)),
            "last_path": state.get("last_path"),
            "root_warnings": state.get("root_warnings", []),
            "started_at": state.get("started_at"),
            "completed_at": state.get("completed_at"),
            "next_refresh_at": state.get("next_refresh_at"),
            "batch_processed": processed,
            "cycle_complete": bool(complete),
            "automatic_mutations": False,
            "git_operations": "read-only",
        }

    def get_status(self) -> dict[str, Any]:
        with self._connection() as db:
            return self._status_from_db(db, self._read_state(db))

    def list_repositories(self, limit: int = 50) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 200))
        with self._connection() as db:
            rows = db.execute("""
                SELECT path, root, name, branch, head_sha, dirty, origin, protected,
                       stack_json, summary, scan_status, scan_error, last_seen_at, scan_count
                FROM repositories ORDER BY path COLLATE NOCASE LIMIT ?
            """, (limit,)).fetchall()
        results = []
        for row in rows:
            try:
                stack = json.loads(row["stack_json"])
            except (TypeError, json.JSONDecodeError):
                stack = []
            results.append({
                "path": row["path"], "root": row["root"], "name": row["name"],
                "branch": row["branch"], "head_sha": row["head_sha"],
                "dirty": bool(row["dirty"]), "origin": row["origin"],
                "protected": bool(row["protected"]), "stack": stack,
                "summary": row["summary"], "scan_status": row["scan_status"],
                "scan_error": row["scan_error"], "last_seen_at": row["last_seen_at"],
                "scan_count": row["scan_count"],
            })
        return results

    def run_once(self) -> dict[str, Any]:
        """Complete the current inventory cycle, resuming its durable cursor."""
        result = self.get_status()
        while result.get("status") != "complete":
            result = self.run_batch()
        return result

    def start(self) -> bool:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return False
            self._stop.clear()
            self._thread = threading.Thread(
                target=self._run,
                name="DGMRepositoryLearning",
                daemon=True,
            )
            self._thread.start()
            return True

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                result = self.run_batch()
                if result.get("cycle_complete"):
                    wait = self.refresh_seconds
                elif result.get("batch_processed", 0):
                    wait = 0.25
                else:
                    wait = 10
                self._stop.wait(wait)
            except Exception:
                self._stop.wait(30)

    def stop(self, timeout: float = 5.0) -> None:
        self._stop.set()
        thread = self._thread
        if thread and thread.is_alive():
            thread.join(timeout=max(0.1, min(float(timeout), 10.0)))
