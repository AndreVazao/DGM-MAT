"""Read-only status and operator controls for progressive repository learning."""
from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException, Query

from core.autonomy.repository_learning import RepositoryLearningService

router = APIRouter(prefix="/runtime/repository-learning", tags=["repository-learning"])
repository_learning_service = RepositoryLearningService()


def _resolve_project_query(query: str, projects: list[dict]) -> dict:
    """Resolve only explicit whole-name/alias mentions; never use fuzzy guesses."""
    normalized = " ".join(str(query).split())
    matches: dict[str, dict] = {}
    for project in projects:
        project_id = str(project.get("project_id") or "")
        if not project_id:
            continue
        aliases = {
            str(value).strip()
            for value in [project.get("name"), project_id, *(project.get("aliases") or [])]
            if isinstance(value, str) and value.strip()
        }
        matched = sorted(
            (
                alias for alias in aliases
                if re.search(
                    r"(?<![\w-])" + re.escape(alias) + r"(?![\w-])",
                    normalized,
                    flags=re.IGNORECASE,
                )
            ),
            key=lambda value: (-len(value), value.casefold()),
        )
        if matched:
            matches[project_id] = {
                "project_id": project_id,
                "name": str(project.get("name") or project_id),
                "matched_aliases": matched,
            }

    candidates = sorted(matches.values(), key=lambda item: item["name"].casefold())
    if not candidates:
        return {"status": "not_found", "query": normalized, "candidates": []}
    if len(candidates) > 1:
        return {"status": "ambiguous", "query": normalized, "candidates": candidates}
    return {"status": "resolved", "query": normalized, "project": candidates[0]}


@router.get("")
def repository_learning_status(limit: int = Query(default=200, ge=1, le=200)):
    """Return durable scan progress, repository metadata and evidence-based group suggestions."""
    status = repository_learning_service.get_status()
    repositories = repository_learning_service.list_repositories(limit)
    groups: dict[str, dict] = {}
    for repository in repositories:
        key = str(repository["project_group_id"])
        group = groups.setdefault(key, {
            "id": key,
            "name": repository["project_group"],
            "basis": repository["project_group_basis"],
            "confidence": repository["project_group_confidence"],
            "repositories": [],
        })
        group["repositories"].append(repository["name"])
        if repository["project_group_confidence"] < group["confidence"]:
            group["confidence"] = repository["project_group_confidence"]
    status["repositories"] = repositories
    status["project_groups"] = sorted(groups.values(), key=lambda item: item["name"].casefold())
    return status


@router.get("/dossier")
def project_dossier(
    project_id: str | None = Query(default=None, min_length=1, max_length=100),
    query: str | None = Query(default=None, min_length=2, max_length=300),
    conversation_limit: int = Query(default=100, ge=1, le=500),
    snapshot_limit: int = Query(default=20, ge=1, le=100),
    finding_limit: int = Query(default=50, ge=1, le=200),
):
    """Return a bounded dossier by exact project ID or unambiguous natural-language alias."""
    from core.repository_intelligence.project_dossier import ProjectDossierError, build_project_dossier
    from core.vault.catalog import VaultCatalog

    if bool(project_id) == bool(query):
        raise HTTPException(status_code=400, detail="Supply exactly one of project_id or query")
    vault_root = VaultCatalog.default_root()
    if not (vault_root / "index" / "catalog.sqlite3").is_file():
        raise HTTPException(status_code=503, detail="Persistent Vault is not initialized")
    vault = VaultCatalog(vault_root=vault_root)
    resolution = None
    if query is not None:
        resolution = _resolve_project_query(query, vault.list_projects())
        if resolution["status"] != "resolved":
            return resolution
        project_id = resolution["project"]["project_id"]

    try:
        dossier = build_project_dossier(
            vault=vault,
            project_id=project_id or "",
            conversation_limit=conversation_limit,
            snapshot_limit=snapshot_limit,
            finding_limit=finding_limit,
            repository_inventory=repository_learning_service.list_repositories(200),
        )
        if resolution is not None:
            dossier["resolution"] = resolution
        return dossier
    except ProjectDossierError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Vault evidence is unavailable") from exc


@router.get("/tree")
def repository_tree(repo_path: str = Query(min_length=1, max_length=1024)):
    """Return a bounded tree artifact for a repository already in the inventory."""
    try:
        return repository_learning_service.read_tree(repo_path)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Repository tree not found") from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Repository tree artifact is missing") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/start")
def start_repository_learning():
    """Start or resume the incremental metadata-only repository worker."""
    started = repository_learning_service.start()
    return {
        "status": "started" if started else "already_running",
        "progress": repository_learning_service.get_status(),
    }


@router.post("/stop")
def stop_repository_learning():
    """Pause the worker without discarding its durable cursor or learned metadata."""
    repository_learning_service.stop()
    return {
        "status": "stopped",
        "progress": repository_learning_service.get_status(),
    }


@router.post("/audit")
def static_project_audit(
    project_id: str = Query(min_length=1, max_length=100),
    snapshot_id: str | None = Query(default=None, min_length=1, max_length=100),
    max_files: int = Query(default=5000, ge=1, le=20000),
    max_file_bytes: int = Query(default=1_000_000, ge=1024, le=5_000_000),
):
    """Run a bounded, read-only static audit against an existing Vault tree snapshot."""
    from core.repository_intelligence.static_audit import StaticAuditError, audit_project
    from core.vault.catalog import VaultCatalog

    vault_root = VaultCatalog.default_root()
    if not (vault_root / "index" / "catalog.sqlite3").is_file():
        raise HTTPException(status_code=503, detail="Persistent Vault is not initialized")
    try:
        report = audit_project(
            vault=VaultCatalog(vault_root=vault_root),
            project_id=project_id,
            snapshot_id=snapshot_id,
            max_files=max_files,
            max_file_bytes=max_file_bytes,
        )
    except StaticAuditError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Vault snapshot or repository file is unavailable") from exc
    return {
        "status": "complete",
        "project_id": report["project_id"],
        "snapshot_id": report["snapshot_id"],
        "tree_fingerprint": report["tree_fingerprint"],
        "audit_fingerprint": report["audit_fingerprint"],
        "files_inspected": report["files_inspected"],
        "files_skipped": report["files_skipped"],
        "summary": report["summary"],
        "findings": report["findings"][:200],
        "findings_truncated": len(report["findings"]) > 200,
        "report_path": report["report_path"],
        "markdown_path": report["markdown_path"],
        "reused": report["reused"],
        "read_only": True,
        "code_executed": False,
    }
