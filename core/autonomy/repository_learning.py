"""Persistent, incremental repository learning for the DGM-MAT runtime.

The worker inventories repository metadata and a short redacted README summary.
It never edits repositories, changes Git state, runs project code, or follows
symlinked directories. A SQLite ledger makes progress resumable across restarts.
"""
from __future__ import annotations

import hashlib
import heapq
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
TREE_MAX_ENTRIES = 4000
TREE_MAX_DEPTH = 12
TREE_SKIP_NAMES = {
    ".env", ".secrets", "secrets", "credentials", ".ssh", ".aws",
    ".dgm-mat", "dgm-mat-full-mirror",
}
TREE_SECRET_FILE_PATTERNS = (
    re.compile(r"(?i)^\.env(?:\..*)?$"),
    re.compile(r"(?i).*(?:secret|credential|password|token).*\.(?:json|ya?ml|toml|ini|txt)$"),
    re.compile(r"(?i).+\.(?:pem|key|p12|pfx|keystore|jks)$"),
    re.compile(r"(?i)^(?:id_rsa|id_ed25519)(?:\.pub)?$"),
    re.compile(r"(?i).*\.tfstate(?:\.backup)?$"),
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

def _specific_origin_key(value: str) -> str | None:
    """Return a grouping key only when an origin identifies a repository.

    Host-only and owner/group-only remotes are too broad to prove that two
    checkouts are the same project. Require at least host/owner/repository.
    """
    parts = [part.casefold() for part in value.strip().strip("/").split("/") if part]
    if len(parts) < 3:
        return None
    return "/".join(parts)


class RepositoryLearningService:
    """Incrementally inventory repositories and skip unchanged snapshots."""

    def __init__(
        self,
        *,
        storage_dir: str | Path | None = None,
        roots: list[str | Path] | tuple[str | Path, ...] | None = None,
        batch_size: int = 5,
        max_depth: int = 8,
        refresh_seconds: int = 900,
        command_timeout: float = 4.0,
    ) -> None:
        base = Path(storage_dir) if storage_dir else storage_manager.get_path("cognition") / "repository_learning"
        base.mkdir(parents=True, exist_ok=True)
        self.database_path = base / "repository_learning.sqlite3"
        configured_tree_dir = os.getenv("DGM_REPOSITORY_TREE_DIR", "").strip()
        self.tree_dir = (
            Path(configured_tree_dir).expanduser().resolve()
            if configured_tree_dir else base / "trees"
        )
        self.tree_dir.mkdir(parents=True, exist_ok=True)
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
        try:
            configured_timeout = float(os.getenv("DGM_REPOSITORY_LEARNING_COMMAND_TIMEOUT", str(command_timeout)))
        except (TypeError, ValueError):
            configured_timeout = float(command_timeout)
        self.command_timeout = max(1.0, min(configured_timeout, 10.0))
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
                CREATE TABLE IF NOT EXISTS repository_artifacts (
                    repo_path TEXT PRIMARY KEY,
                    tree_path TEXT NOT NULL,
                    tree_sha256 TEXT NOT NULL,
                    entry_count INTEGER NOT NULL DEFAULT 0,
                    truncated INTEGER NOT NULL DEFAULT 0,
                    generated_at TEXT NOT NULL,
                    tree_error TEXT
                );
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
                        if name.casefold() not in SKIP_DIRS
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

    def _tree_artifact_path(self, path: Path) -> Path:
        identity = hashlib.sha256(str(path.resolve()).casefold().encode("utf-8")).hexdigest()[:10]
        slug = re.sub(r"[^A-Za-z0-9._-]+", "-", path.name).strip("-.")[:64] or "repository"
        return self.tree_dir / f"{slug}-{identity}.tree.txt"

    @staticmethod
    def _skip_tree_file(name: str) -> bool:
        folded = name.casefold()
        if folded in TREE_SKIP_NAMES:
            return True
        return any(pattern.fullmatch(name) for pattern in TREE_SECRET_FILE_PATTERNS)

    def _write_tree(self, path: Path) -> dict[str, Any]:
        """Write a bounded path-only tree outside the source repository."""
        destination = self._tree_artifact_path(path)
        lines = [
            "# DGM-MAT repository tree",
            f"Repository: {path.name}",
            f"Source: {path}",
            f"Generated: {_now()}",
            "Contents: paths only; no file contents are read",
            ".",
        ]
        entry_count = 0
        truncated = False

        def collect_visible(folder: Path, limit: int) -> tuple[list[tuple[str, str, str, bool]], bool]:
            """Collect at most limit+1 sorted entries, even for huge directories."""
            unreadable = False

            def candidates():
                nonlocal unreadable
                try:
                    with os.scandir(folder) as scanner:
                        for entry in scanner:
                            name = entry.name
                            if name.casefold() in SKIP_DIRS or name.casefold() in TREE_SKIP_NAMES:
                                continue
                            if path.name.casefold() == "dgm-mat" and folder == path and name.casefold() == "storage":
                                continue
                            if self._skip_tree_file(name):
                                continue
                            try:
                                if entry.is_symlink():
                                    continue
                                is_dir = entry.is_dir(follow_symlinks=False)
                            except OSError:
                                continue
                            yield (name.casefold(), name, entry.path, is_dir)
                except OSError:
                    unreadable = True

            # nsmallest keeps memory bounded by the remaining tree budget + 1.
            return heapq.nsmallest(max(1, limit + 1), candidates()), unreadable

        def visit(folder: Path, prefix: str, depth: int) -> None:
            nonlocal entry_count, truncated
            if truncated:
                return
            if depth >= TREE_MAX_DEPTH:
                remaining, unreadable = collect_visible(folder, 0)
                if unreadable:
                    lines.append(prefix + "[directory unreadable]")
                if remaining:
                    truncated = True
                return

            remaining_budget = max(0, TREE_MAX_ENTRIES - entry_count)
            visible, unreadable = collect_visible(folder, remaining_budget)
            if unreadable:
                lines.append(prefix + "[directory unreadable]")
            has_more = len(visible) > remaining_budget
            visible = visible[:remaining_budget]

            for index, (_, name, entry_path, is_dir) in enumerate(visible):
                is_last = index == len(visible) - 1 and not has_more
                connector = "└── " if is_last else "├── "
                lines.append(prefix + connector + name + ("/" if is_dir else ""))
                entry_count += 1
                if is_dir:
                    child_prefix = prefix + ("    " if is_last else "│   ")
                    visit(Path(entry_path), child_prefix, depth + 1)
                    if truncated:
                        return

            if has_more:
                truncated = True

        visit(path, "", 0)
        if truncated:
            lines.append("... [truncated: entry limit or maximum depth reached]")
        content = "\n".join(lines) + "\n"
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.write_text(content, encoding="utf-8")
        temporary.replace(destination)
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        generated_at = _now()
        with self._connection() as db:
            db.execute(
                """
                INSERT INTO repository_artifacts(
                    repo_path, tree_path, tree_sha256, entry_count, truncated, generated_at, tree_error
                ) VALUES (?, ?, ?, ?, ?, ?, NULL)
                ON CONFLICT(repo_path) DO UPDATE SET
                    tree_path=excluded.tree_path, tree_sha256=excluded.tree_sha256,
                    entry_count=excluded.entry_count, truncated=excluded.truncated,
                    generated_at=excluded.generated_at, tree_error=NULL
                """,
                (str(path), str(destination), digest, entry_count, int(truncated), generated_at),
            )
            db.commit()
        return {
            "tree_path": str(destination),
            "tree_sha256": digest,
            "tree_entries": entry_count,
            "tree_truncated": truncated,
            "tree_generated_at": generated_at,
            "tree_error": None,
        }

    def _ensure_tree(self, path: Path, *, protected: bool, force: bool = False) -> None:
        if protected:
            return
        with self._connection() as db:
            row = db.execute(
                "SELECT tree_path FROM repository_artifacts WHERE repo_path=?",
                (str(path),),
            ).fetchone()
        if not force and row and Path(row["tree_path"]).is_file():
            return
        self._write_tree(path)

    def _record_tree_error(self, path: Path, error: Exception) -> None:
        destination = self._tree_artifact_path(path)
        with self._connection() as db:
            db.execute(
                """
                INSERT INTO repository_artifacts(
                    repo_path, tree_path, tree_sha256, entry_count, truncated, generated_at, tree_error
                ) VALUES (?, ?, '', 0, 0, ?, ?)
                ON CONFLICT(repo_path) DO UPDATE SET
                    tree_path=excluded.tree_path, tree_error=excluded.tree_error,
                    generated_at=excluded.generated_at
                """,
                (str(path), str(destination), _now(), type(error).__name__),
            )
            db.commit()

    def _inspect(self, item: dict[str, str]) -> dict[str, Any]:
        path = Path(item["path"])
        protected = self._is_protected(path)
        branch = self._git(path, "branch", "--show-current") or "detached"
        status_output = self._git(path, "status", "--porcelain=v1", "-uno")
        dirty = bool(status_output)
        try:
            head = self._git(path, "rev-parse", "--short=12", "HEAD") or "unknown"
        except RuntimeError:
            # A newly initialized repository has a symbolic branch but no commit yet.
            # Git status succeeds in this state; represent it as an unborn branch.
            if branch != "detached":
                head = "unborn"
            else:
                raise
        try:
            origin = _safe_origin(self._git(path, "remote", "get-url", "origin"))
        except (RuntimeError, subprocess.TimeoutExpired):
            origin = ""
        stack = self._manifest_stack(path)
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
            "summary": None,
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
                    if not unchanged:
                        inspected["summary"] = self._read_project_summary(
                            Path(inspected["path"]), bool(inspected["protected"])
                        )
                    try:
                        self._ensure_tree(
                            Path(inspected["path"]),
                            protected=bool(inspected["protected"]),
                            force=not unchanged,
                        )
                    except (OSError, RuntimeError, ValueError) as tree_exc:
                        self._record_tree_error(Path(inspected["path"]), tree_exc)
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
                    error_code = str(exc)[:120] if isinstance(exc, RuntimeError) else type(exc).__name__
                    db.execute(
                        "UPDATE repositories SET scan_error=? WHERE path=?",
                        (error_code, path_text),
                    )
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
        candidate_items = state.get("candidate_paths", [])
        next_item = candidate_items[cursor] if isinstance(candidate_items, list) and cursor < len(candidate_items) else None
        progress_percent = 100.0 if complete else (
            round((min(cursor, total) / total) * 100, 1) if total else 0.0
        )
        return {
            "status": state.get("status", "not_started"),
            "run_id": state.get("run_id"),
            "scan_roots": [str(root) for root in self.roots],
            "total_candidates": total,
            "processed_candidates": min(cursor, total),
            "pending_candidates": max(0, total - cursor),
            "progress_percent": progress_percent,
            "next_path": next_item.get("path") if isinstance(next_item, dict) else None,
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
                SELECT r.path, r.root, r.name, r.branch, r.head_sha, r.dirty, r.origin, r.protected,
                       r.stack_json, r.summary, r.scan_status, r.scan_error, r.last_seen_at, r.scan_count,
                       a.tree_path, a.tree_sha256, a.entry_count AS tree_entries,
                       a.truncated AS tree_truncated, a.generated_at AS tree_generated_at,
                       a.tree_error
                FROM repositories AS r
                LEFT JOIN repository_artifacts AS a ON a.repo_path=r.path
                ORDER BY r.path COLLATE NOCASE LIMIT ?
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
                "tree_path": row["tree_path"], "tree_sha256": row["tree_sha256"],
                "tree_entries": row["tree_entries"],
                "tree_truncated": bool(row["tree_truncated"]) if row["tree_truncated"] is not None else False,
                "tree_generated_at": row["tree_generated_at"], "tree_error": row["tree_error"],
                "project_group": None,
                "project_group_id": None,
                "project_group_basis": "awaiting_relationship_evidence",
                "project_group_confidence": 0.0,
            })

        origin_members: dict[str, list[dict[str, Any]]] = {}
        parent_members: dict[str, list[dict[str, Any]]] = {}
        for item in results:
            origin_key = _specific_origin_key(str(item["origin"] or ""))
            if origin_key:
                origin_members.setdefault(origin_key, []).append(item)
            parent_path = Path(item["path"]).parent
            parent = str(parent_path).casefold()
            root_path = str(Path(item["root"])).casefold()
            if parent != root_path and parent_path.name.casefold() not in {
                "_worktrees", "worktrees", "repos", "repositories", "clones", "archive", "archives"
            }:
                parent_members.setdefault(parent, []).append(item)

        for members in origin_members.values():
            if len(members) > 1:
                label = Path(members[0]["path"]).name
                for item in members:
                    item["project_group"] = label
                    item["project_group_id"] = f"origin:{_specific_origin_key(str(item['origin']))}"
                    item["project_group_basis"] = "same_git_origin"
                    item["project_group_confidence"] = 0.99

        for members in parent_members.values():
            if len(members) > 1:
                label = Path(members[0]["path"]).parent.name
                for item in members:
                    if item["project_group"] is None:
                        item["project_group"] = label
                        item["project_group_id"] = f"folder:{str(Path(item['path']).parent).casefold()}"
                        item["project_group_basis"] = "shared_parent_folder"
                        item["project_group_confidence"] = 0.85

        for item in results:
            if item["project_group"] is None:
                item["project_group"] = item["name"]
                item["project_group_id"] = f"repo:{item['path'].casefold()}"
                item["project_group_basis"] = "single_repository_pending_semantic_review"
                item["project_group_confidence"] = 0.25
        return results

    def read_tree(self, repo_path: str, *, max_bytes: int = 2_000_000) -> dict[str, Any]:
        """Read only a tree artifact already indexed for a known repository."""
        with self._connection() as db:
            row = db.execute(
                "SELECT tree_path, tree_sha256, tree_error FROM repository_artifacts WHERE repo_path=?",
                (str(Path(repo_path).resolve()),),
            ).fetchone()
        if row is None or not row["tree_path"]:
            raise KeyError("repository_tree_not_found")
        if row["tree_error"]:
            raise ValueError("repository_tree_generation_failed")
        artifact = Path(row["tree_path"]).resolve()
        if not artifact.is_relative_to(self.tree_dir.resolve()):
            raise ValueError("repository_tree_path_outside_artifact_directory")
        if not artifact.is_file():
            raise FileNotFoundError("repository_tree_artifact_missing")
        if artifact.stat().st_size > max(1, int(max_bytes)):
            raise ValueError("repository_tree_artifact_too_large")
        return {
            "repo_path": str(Path(repo_path).resolve()),
            "tree_path": str(artifact),
            "tree_sha256": row["tree_sha256"],
            "content": artifact.read_text(encoding="utf-8"),
        }

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

    def stop(self, timeout: float | None = 5.0) -> bool:
        """Request stop and report only after the worker has exited."""
        self._stop.set()
        thread = self._thread
        if thread and thread.is_alive():
            thread.join(timeout=None if timeout is None else max(0.1, min(float(timeout), 10.0)))
        return thread is None or not thread.is_alive()
