# Path: C:\ProgramasGodMode\DGM-MAT\core\repository_intelligence\snapshot.py
"""Safe deterministic repository inventory and tree snapshots."""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


DEFAULT_IGNORES = {
    ".git", ".hg", ".svn", ".venv", "venv", "env", "node_modules",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "dist", "build", "coverage", ".next", ".turbo",
}
SENSITIVE_NAMES = {
    ".env", ".env.local", ".env.production", "id_rsa", "id_ed25519",
    "credentials.json", "secrets.json", "bootstrap.token",
}


@dataclass(frozen=True, slots=True)
class InventoryEntry:
    path: str
    kind: str
    size_bytes: int | None
    suffix: str
    sensitive_name: bool = False


@dataclass(frozen=True, slots=True)
class InventoryReport:
    root: str
    generated_at: str
    files: int
    directories: int
    skipped: int
    entries: tuple[InventoryEntry, ...]

    def to_dict(self) -> dict:
        data = asdict(self)
        data["entries"] = [asdict(entry) for entry in self.entries]
        return data


class RepositorySnapshotError(ValueError):
    pass


def build_inventory(
    root: str | Path,
    *,
    max_depth: int = 12,
    max_entries: int = 50_000,
    ignore_names: Iterable[str] = (),
) -> InventoryReport:
    """Inventory one explicit root without reading contents or following links."""
    root_path = Path(root).expanduser().resolve(strict=True)
    if not root_path.is_dir():
        raise RepositorySnapshotError("Repository root must be a directory.")
    if max_depth < 0 or max_entries < 1:
        raise RepositorySnapshotError("max_depth must be >= 0 and max_entries >= 1.")

    ignores = DEFAULT_IGNORES | {name.casefold() for name in ignore_names}
    entries: list[InventoryEntry] = []
    skipped = 0
    stack: list[tuple[Path, int]] = [(root_path, 0)]

    while stack:
        current, depth = stack.pop()
        try:
            with os.scandir(current) as iterator:
                children = sorted(iterator, key=lambda entry: entry.name.casefold(), reverse=True)
        except OSError:
            skipped += 1
            continue

        for child in children:
            if child.name.casefold() in ignores:
                skipped += 1
                continue
            try:
                relative = Path(child.path).relative_to(root_path).as_posix()
                if child.is_symlink():
                    entries.append(InventoryEntry(
                        relative, "symlink", None, Path(child.name).suffix.casefold(),
                        child.name.casefold() in SENSITIVE_NAMES,
                    ))
                elif child.is_dir(follow_symlinks=False):
                    entries.append(InventoryEntry(relative, "directory", None, "", False))
                    if depth < max_depth:
                        stack.append((Path(child.path), depth + 1))
                    else:
                        skipped += 1
                elif child.is_file(follow_symlinks=False):
                    try:
                        size = child.stat(follow_symlinks=False).st_size
                    except OSError:
                        size = None
                        skipped += 1
                    lower_name = child.name.casefold()
                    entries.append(InventoryEntry(
                        relative, "file", size, Path(child.name).suffix.casefold(),
                        lower_name in SENSITIVE_NAMES or lower_name.startswith(".env."),
                    ))
                else:
                    skipped += 1
            except OSError:
                skipped += 1
            if len(entries) >= max_entries:
                return _report(root_path, entries, skipped, max_entries)
    return _report(root_path, entries, skipped, max_entries)


def _report(root: Path, entries: list[InventoryEntry], skipped: int, limit: int) -> InventoryReport:
    entries.sort(key=lambda item: (item.path.casefold(), item.kind))
    entries = entries[:limit]
    return InventoryReport(
        root=str(root),
        generated_at=datetime.now(timezone.utc).isoformat(),
        files=sum(entry.kind == "file" for entry in entries),
        directories=sum(entry.kind == "directory" for entry in entries),
        skipped=skipped,
        entries=tuple(entries),
    )


def render_tree(report: InventoryReport) -> str:
    """Render a stable text tree; sensitive files are named but never read."""
    root_name = Path(report.root).name or report.root
    children: dict[str, list[InventoryEntry]] = {}
    for entry in report.entries:
        parent = str(Path(entry.path).parent).replace("\\", "/")
        if parent == ".":
            parent = ""
        children.setdefault(parent, []).append(entry)

    lines = [root_name]

    def render(parent: str, depth: int) -> None:
        for entry in sorted(children.get(parent, []), key=lambda item: (item.kind != "directory", item.path.casefold())):
            name = Path(entry.path).name
            suffix = "/" if entry.kind == "directory" else " @" if entry.kind == "symlink" else ""
            marker = " [SENSITIVE NAME]" if entry.sensitive_name else ""
            lines.append(f"{'  ' * depth}- {name}{suffix}{marker}")
            if entry.kind == "directory":
                render(entry.path, depth + 1)

    render("", 0)
    if report.skipped:
        lines.append(f"[skipped: {report.skipped}]")
    return "\n".join(lines)


def write_inventory(report: InventoryReport, *, json_path: str | Path, tree_path: str | Path) -> tuple[Path, Path]:
    """Write reports to explicit destinations and refuse silent overwrites."""
    json_target, tree_target = Path(json_path), Path(tree_path)
    if json_target.resolve() == tree_target.resolve():
        raise RepositorySnapshotError("JSON and tree outputs must be different paths.")
    if json_target.exists() or tree_target.exists():
        raise FileExistsError("Inventory output already exists; choose new paths to preserve prior evidence.")
    json_target.parent.mkdir(parents=True, exist_ok=True)
    tree_target.parent.mkdir(parents=True, exist_ok=True)
    json_target.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tree_target.write_text(render_tree(report) + "\n", encoding="utf-8")
    return json_target, tree_target
