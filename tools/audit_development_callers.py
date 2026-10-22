"""Read-only AST inventory for legacy development API callers.

Run from a checkout:
    python tools/audit_development_callers.py --root . --format text

This is a static inventory, not proof of runtime reachability. Dynamic imports,
reflection, generated code and configuration-driven wiring may not be visible.
The script never imports or executes project modules and never writes files.
"""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any

DEFAULT_SYMBOLS = {
    "DevelopmentEngine": {"process_request"},
    "ImplementationEngine": {"execute_implementation"},
    "CodeGenerationEngine": {"generate_code"},
    "DeadCodeDetector": {"find_dead_code"},
    "ValidationEngine": {"validate_implementation"},
    "TaskStore": {"create", "get", "transition", "list_events"},
}
EXCLUDED_DIRS = {
    ".git", ".hg", ".svn", ".venv", "venv", "env", "node_modules",
    "__pycache__", "build", "dist", "site-packages",
}


def _inside_excluded(path: Path) -> bool:
    return any(part in EXCLUDED_DIRS for part in path.parts)


def scan_python_files(root: Path) -> list[Path]:
    """Return sorted Python source files without following excluded directories."""
    files: list[Path] = []
    for path in root.rglob("*.py"):
        try:
            relative = path.relative_to(root)
        except ValueError:
            continue
        if not _inside_excluded(relative):
            files.append(path)
    return sorted(files)


def inspect_file(path: Path, root: Path) -> list[dict[str, Any]]:
    """Collect imports, class declarations, and references to tracked methods."""
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError, UnicodeError) as exc:
        return [{
            "path": path.relative_to(root).as_posix(),
            "line": getattr(exc, "lineno", None),
            "kind": "parse_error",
            "symbol": "",
            "detail": str(exc),
        }]

    relative = path.relative_to(root).as_posix()
    findings: list[dict[str, Any]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                findings.append({
                    "path": relative, "line": node.lineno, "kind": "import",
                    "symbol": alias.name, "detail": "import statement",
                })
        elif isinstance(node, ast.ImportFrom):
            module = "." * node.level + (node.module or "")
            for alias in node.names:
                findings.append({
                    "path": relative, "line": node.lineno, "kind": "from_import",
                    "symbol": f"{module}:{alias.name}", "detail": "from-import statement",
                })
        elif isinstance(node, ast.ClassDef) and node.name in DEFAULT_SYMBOLS:
            findings.append({
                "path": relative, "line": node.lineno, "kind": "class_definition",
                "symbol": node.name, "detail": "tracked class declaration",
            })
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Attribute):
                method = function.attr
                if any(method in methods for methods in DEFAULT_SYMBOLS.values()):
                    findings.append({
                        "path": relative, "line": node.lineno, "kind": "method_call",
                        "symbol": method, "detail": ast.unparse(function),
                    })
            elif isinstance(function, ast.Name) and function.id in DEFAULT_SYMBOLS:
                findings.append({
                    "path": relative, "line": node.lineno, "kind": "class_call",
                    "symbol": function.id, "detail": "class/constructor call",
                })

    return findings


def build_report(root: Path) -> dict[str, Any]:
    root = root.resolve()
    files = scan_python_files(root)
    findings: list[dict[str, Any]] = []
    for path in files:
        findings.extend(inspect_file(path, root))
    findings.sort(key=lambda item: (
        item["path"], item["line"] or 0, item["kind"], item["symbol"]
    ))
    return {
        "root": str(root),
        "python_files_scanned": len(files),
        "finding_count": len(findings),
        "limitations": [
            "Static AST results do not prove runtime reachability.",
            "Dynamic imports, reflection, generated code and configuration wiring may be missed.",
            "Import statements are inventoried broadly; review paths and symbols manually.",
        ],
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="checkout root (default: current directory)")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    if not root.is_dir():
        parser.error(f"root is not a directory: {root}")
    report = build_report(root)
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"Root: {report['root']}")
        print(f"Python files scanned: {report['python_files_scanned']}")
        print(f"Findings: {report['finding_count']}")
        for finding in report["findings"]:
            line = finding["line"] if finding["line"] is not None else "?"
            print(f"{finding['path']}:{line}: {finding['kind']}: {finding['symbol']} — {finding['detail']}")
        print("Limitations:")
        for limitation in report["limitations"]:
            print(f"- {limitation}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
