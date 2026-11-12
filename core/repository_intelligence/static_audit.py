"""Read-only static audits tied to immutable Vault repository snapshots."""
from __future__ import annotations

import ast
import hashlib
import json
import re
import tomllib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.vault.catalog import VaultCatalog

SCANNER_VERSION = "1.0.0"
IGNORED = {".git", ".venv", "venv", "node_modules", "__pycache__", "build", "dist", "target", "vendor", ".next", "coverage"}
SENSITIVE = {".env", ".env.local", ".env.production", "credentials.json", "secrets.json", "id_rsa", "id_ed25519", "bootstrap.token"}
PYTHON = {".py", ".pyi"}
JAVASCRIPT = {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx"}
JS_EXTENSIONS = ("", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".json")
JS_IMPORT = re.compile(r"""(?:\bfrom\s*|\bimport\s*|\bimport\s*\()\s*['"]([^'"]+)['"]""")
JS_EXPORT = re.compile(r"^\s*export\s+(?:\*|\{[^}]*\}|\b(?:default|const|let|var|function|class|async\s+function|interface|type|enum)\b)", re.MULTILINE)


class StaticAuditError(ValueError):
    pass


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _safe_file(root: Path, relative: str) -> Path | None:
    item = Path(relative)
    if item.is_absolute() or ".." in item.parts:
        return None
    if any(part.casefold() in IGNORED or part.casefold() in SENSITIVE for part in item.parts):
        return None
    target = root / item
    try:
        resolved = target.resolve(strict=True)
        if target.is_symlink() or not resolved.is_relative_to(root) or not resolved.is_file():
            return None
        return resolved
    except (OSError, RuntimeError):
        return None


def _read(path: Path, limit: int) -> tuple[str | None, str | None]:
    try:
        if path.stat().st_size > limit:
            return None, "file_too_large"
        return path.read_text(encoding="utf-8-sig"), None
    except UnicodeDecodeError:
        return None, "non_utf8_source"
    except OSError:
        return None, "read_error"


def _python(relative: str, source: str) -> dict[str, Any]:
    try:
        tree = ast.parse(source, filename=relative)
    except SyntaxError as exc:
        return {"path": relative, "syntax": "error", "imports": [], "definitions": [], "exports": [],
                "findings": [{"kind": "python_syntax_error", "confidence": "confirmed",
                              "line": exc.lineno, "message": exc.msg}]}
    imports, definitions, explicit_exports = [], [], None
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend({"module": alias.name, "line": node.lineno, "relative": False} for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append({"module": node.module or "", "line": node.lineno, "relative": node.level > 0,
                            "level": node.level, "names": [alias.name for alias in node.names]})
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            definitions.append({"name": node.name, "kind": type(node).__name__, "line": node.lineno})
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(target, ast.Name) and target.id == "__all__" for target in targets):
                value = node.value
                if isinstance(value, (ast.List, ast.Tuple)):
                    explicit_exports = [x.value for x in value.elts if isinstance(x, ast.Constant) and isinstance(x.value, str)]
    exports = explicit_exports if explicit_exports is not None else sorted(x["name"] for x in definitions if not x["name"].startswith("_"))
    return {"path": relative, "syntax": "ok", "imports": sorted(imports, key=lambda x: (x["line"], x["module"])),
            "definitions": sorted(definitions, key=lambda x: (x["line"], x["name"])),
            "exports": exports, "findings": []}


def _js(relative: str, source: str) -> dict[str, Any]:
    imports = [{"specifier": m.group(1), "line": source.count("\n", 0, m.start()) + 1} for m in JS_IMPORT.finditer(source)]
    exports = [{"line": source.count("\n", 0, m.start()) + 1, "declaration": m.group(0).strip()[:120]} for m in JS_EXPORT.finditer(source)]
    return {"path": relative, "imports": imports, "exports": exports, "findings": []}


def _resolve_js(root: Path, source: str, specifier: str) -> bool:
    if not specifier.startswith("."):
        return True
    base = (root / source).parent / specifier
    candidates = [base] if base.suffix else [base.with_suffix(ext) if ext else base for ext in JS_EXTENSIONS]
    if base.is_dir():
        candidates.extend(base / ("index" + ext) for ext in JS_EXTENSIONS if ext)
    for candidate in candidates:
        try:
            resolved = candidate.resolve(strict=True)
            if resolved.is_relative_to(root) and resolved.is_file() and not candidate.is_symlink():
                return True
        except (OSError, RuntimeError):
            continue
    return False


def _manifests(files: dict[str, Path], max_bytes: int) -> dict[str, Any]:
    result: dict[str, Any] = {"python": [], "javascript": [], "warnings": []}
    for relative, path in sorted(files.items()):
        name = path.name.casefold()
        if name not in {"pyproject.toml", "requirements.txt", "requirements-dev.txt", "package.json"}:
            continue
        text, error = _read(path, max_bytes)
        if error:
            result["warnings"].append({"path": relative, "kind": error})
            continue
        try:
            if name == "pyproject.toml":
                payload = tomllib.loads(text or "")
                project = payload.get("project", {})
                values = list(project.get("dependencies", []))
                for group in project.get("optional-dependencies", {}).values():
                    values.extend(group)
                result["python"].extend(str(x).split("[", 1)[0].casefold() for x in values)
            elif name.startswith("requirements"):
                for line in (text or "").splitlines():
                    cleaned = line.split("#", 1)[0].strip()
                    match = re.match(r"^([A-Za-z0-9_.-]+)", cleaned)
                    if match:
                        result["python"].append(match.group(1).casefold())
            else:
                payload = json.loads(text or "{}")
                for field in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
                    result["javascript"].extend(str(x) for x in payload.get(field, {}))
        except (ValueError, TypeError, AttributeError):
            result["warnings"].append({"path": relative, "kind": "manifest_parse_error"})
    result["python"] = sorted(set(result["python"]))
    result["javascript"] = sorted(set(result["javascript"]))
    return result


def _markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Static project audit: " + report["project_id"], "",
        "- Repository: " + report["repository_path"],
        "- Snapshot: " + report["snapshot_id"],
        "- Tree fingerprint: " + report["tree_fingerprint"],
        "- Audit fingerprint: " + report["audit_fingerprint"],
        "- Files inspected: " + str(report["files_inspected"]),
        "- Files skipped: " + str(report["files_skipped"]), "",
        "## Summary",
        "- Python files: " + str(report["summary"]["python_files"]),
        "- JavaScript/TypeScript files: " + str(report["summary"]["javascript_files"]),
        "- Confirmed syntax errors: " + str(report["summary"]["syntax_errors"]),
        "- Unresolved relative imports: " + str(report["summary"]["unresolved_relative_imports"]), "",
        "## Findings",
    ]
    for item in report["findings"]:
        lines.append("- " + item.get("path", "") + ":" + str(item.get("line") or "?") + " — " +
                     item["kind"] + " (" + item["confidence"] + "): " + item.get("message", ""))
    lines.extend(["", "## Limitations",
                  "- Static analysis does not prove runtime reachability or correctness.",
                  "- Dynamic imports, reflection, generated code and conditional wiring may be missed.",
                  "- External and optional dependencies are not declared missing from imports alone.",
                  "- No project code was imported, executed, installed, modified or sent over the network.", ""])
    return "\n".join(lines)


def audit_project(*, vault: VaultCatalog, project_id: str, snapshot_id: str | None = None,
                  max_files: int = 5000, max_file_bytes: int = 1_000_000) -> dict[str, Any]:
    """Audit only a repository represented by a verified immutable Vault snapshot."""
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", project_id):
        raise StaticAuditError("Invalid project identifier.")
    if not 1 <= max_files <= 20000 or not 1024 <= max_file_bytes <= 5_000_000:
        raise StaticAuditError("Audit bounds are outside supported limits.")
    if not vault.get_project(project_id):
        raise StaticAuditError("Unknown Vault project.")
    sql = "SELECT snapshot_id,repository_path,tree_fingerprint,snapshot_path FROM tree_snapshots WHERE project_id=?"
    params: tuple[Any, ...] = (project_id,)
    if snapshot_id:
        sql += " AND snapshot_id=?"
        params = (project_id, snapshot_id)
    sql += " ORDER BY created_at DESC LIMIT 1"
    with vault._connect() as db:
        row = db.execute(sql, params).fetchone()
    if not row:
        raise StaticAuditError("No matching Vault tree snapshot; create a snapshot first.")
    root = Path(row["repository_path"]).resolve(strict=True)
    snapshot_path = Path(row["snapshot_path"]).resolve(strict=True)
    if not snapshot_path.is_relative_to(vault.root.resolve()):
        raise StaticAuditError("Snapshot path is outside the Vault.")
    tree = json.loads(snapshot_path.read_text(encoding="utf-8"))
    if tree.get("project_id") != project_id or Path(tree.get("repository_path", "")).resolve() != root:
        raise StaticAuditError("Snapshot identity does not match the requested project.")

    files: dict[str, Path] = {}
    findings: list[dict[str, Any]] = []
    skipped = 0
    for entry in tree.get("entries", []):
        relative = str(entry.get("path", ""))
        if entry.get("kind", "file") == "directory":
            continue
        path = _safe_file(root, relative)
        if path is None:
            skipped += 1
            continue
        if path.suffix.casefold() in PYTHON | JAVASCRIPT or path.name.casefold() in {
            "pyproject.toml", "requirements.txt", "requirements-dev.txt", "package.json"
        }:
            expected_hash = str(entry.get("sha256") or "")
            if not expected_hash:
                skipped += 1
                findings.append({"path": relative, "kind": "snapshot_hash_missing",
                                 "confidence": "heuristic", "message": "Snapshot contains no content hash; file was not audited."})
                continue
            try:
                if path.stat().st_size > max_file_bytes:
                    skipped += 1
                    findings.append({"path": relative, "kind": "file_too_large",
                                     "confidence": "heuristic", "message": "File exceeds the configured size limit."})
                    continue
                actual_hash = _digest(path.read_bytes())
            except OSError:
                skipped += 1
                findings.append({"path": relative, "kind": "read_error",
                                 "confidence": "heuristic", "message": "File could not be read safely."})
                continue
            if actual_hash != expected_hash:
                skipped += 1
                findings.append({"path": relative, "kind": "snapshot_file_changed",
                                 "confidence": "confirmed", "message": "Current file hash differs from the immutable tree snapshot; file was not audited."})
                continue
            files[relative] = path
    if len(files) > max_files:
        raise StaticAuditError("Candidate file count exceeds configured limit; no report written.")

    python_results, js_results = [], []
    inspected = 0
    for relative, path in sorted(files.items()):
        if path.suffix.casefold() not in PYTHON | JAVASCRIPT:
            continue
        source, error = _read(path, max_file_bytes)
        if error:
            skipped += 1
            findings.append({"path": relative, "kind": error, "confidence": "heuristic", "message": error})
            continue
        inspected += 1
        result = _python(relative, source or "") if path.suffix.casefold() in PYTHON else _js(relative, source or "")
        (python_results if path.suffix.casefold() in PYTHON else js_results).append(result)

    for result in python_results:
        source_path = Path(result["path"])
        for item in result["imports"]:
            if not item.get("relative"):
                continue
            base = root / source_path.parent
            for _ in range(max(0, int(item.get("level", 0)) - 1)):
                base = base.parent
            module = item.get("module", "")
            candidates = [base.joinpath(*module.split(".")).with_suffix(".py"),
                          base.joinpath(*module.split(".")) / "__init__.py"]
            if module and not any(candidate.is_file() for candidate in candidates):
                findings.append({"path": result["path"], "line": item["line"],
                                 "kind": "unresolved_relative_python_import", "confidence": "confirmed",
                                 "message": "Relative import does not resolve to a Python source file: " + module})
    for result in js_results:
        for item in result["imports"]:
            if item["specifier"].startswith(".") and not _resolve_js(root, result["path"], item["specifier"]):
                findings.append({"path": result["path"], "line": item["line"],
                                 "kind": "unresolved_relative_js_import", "confidence": "confirmed",
                                 "message": "Relative import does not resolve to a supported local file: " + item["specifier"]})

    manifests = _manifests(files, max_file_bytes)
    findings.extend({**item, "confidence": "heuristic", "message": item["kind"]} for item in manifests["warnings"])
    for result in python_results:
        for item in result["findings"]:
            findings.append({**item, "confidence": "confirmed", "message": item.get("message", item["kind"])})
    findings.sort(key=lambda x: (x.get("path", "").casefold(), x.get("line") or 0, x["kind"]))
    stable = {"project_id": project_id, "snapshot_id": row["snapshot_id"],
              "tree_fingerprint": row["tree_fingerprint"], "scanner_version": SCANNER_VERSION,
              "files_inspected": inspected, "files_skipped": skipped,
              "python": python_results, "javascript": js_results, "manifests": manifests, "findings": findings}
    fingerprint = _digest(json.dumps(stable, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    report = {**stable, "repository_path": str(root), "audit_fingerprint": fingerprint,
              "generated_at": datetime.now(timezone.utc).isoformat(),
              "summary": {"python_files": len(python_results), "javascript_files": len(js_results),
                          "syntax_errors": sum(x["kind"] == "python_syntax_error" for x in findings),
                          "unresolved_relative_imports": sum(x["kind"].startswith("unresolved_relative_") for x in findings)}}
    folder = vault.root / "projects" / project_id / "audits"
    folder.mkdir(parents=True, exist_ok=True)
    json_path, md_path = folder / (fingerprint + ".json"), folder / (fingerprint + ".md")
    reused = json_path.is_file() and md_path.is_file()
    if not json_path.exists():
        temp = json_path.with_suffix(".json.tmp")
        temp.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        temp.replace(json_path)
    if not md_path.exists():
        temp = md_path.with_suffix(".md.tmp")
        temp.write_text(_markdown(report), encoding="utf-8")
        temp.replace(md_path)
    report["report_path"], report["markdown_path"] = str(json_path), str(md_path)
    report["reused"] = reused
    return report
