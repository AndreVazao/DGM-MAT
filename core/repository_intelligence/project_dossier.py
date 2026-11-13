"""Read-only, evidence-linked project dossier assembled from the local Vault.

This V1 is deliberately a verified-evidence projection, not an AI interpretation:
it never promotes proposals to decisions and never returns transcript bodies.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from core.vault.catalog import VaultCatalog
from core.repository_intelligence.github_live_evidence import fetch_github_live_evidence


class ProjectDossierError(ValueError):
    """Raised when a project dossier cannot be safely assembled."""


def build_project_dossier(
    *,
    vault: VaultCatalog,
    project_id: str,
    conversation_limit: int = 100,
    snapshot_limit: int = 20,
    finding_limit: int = 50,
    repository_inventory: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a bounded project status view from existing Vault evidence only."""
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", project_id or ""):
        raise ProjectDossierError("Invalid project identifier.")
    if not 1 <= conversation_limit <= 500 or not 1 <= snapshot_limit <= 100 or not 1 <= finding_limit <= 200:
        raise ProjectDossierError("Dossier limits are outside supported bounds.")

    project = vault.get_project(project_id)
    if not project:
        raise ProjectDossierError("Unknown Vault project.")

    with vault._connect() as db:
        total = db.execute(
            "SELECT COUNT(*) AS count FROM conversations WHERE project_id=?",
            (project_id,),
        ).fetchone()["count"]
        provider_rows = db.execute(
            "SELECT provider,COUNT(*) AS count FROM conversations WHERE project_id=? "
            "GROUP BY provider ORDER BY provider",
            (project_id,),
        ).fetchall()
        completeness_rows = db.execute(
            "SELECT completeness,COUNT(*) AS count FROM conversations WHERE project_id=? "
            "GROUP BY completeness ORDER BY completeness",
            (project_id,),
        ).fetchall()
        conversation_rows = db.execute(
            "SELECT provider,conversation_id,title,url,completeness,message_count,"
            "source_fingerprint,assignment_status,captured_at "
            "FROM conversations WHERE project_id=? "
            "ORDER BY captured_at DESC,provider,conversation_id LIMIT ?",
            (project_id, conversation_limit),
        ).fetchall()
        reference_rows = db.execute(
            "SELECT r.canonical_url,r.owner,r.repository,r.verification_status,r.html_url,"
            "r.description,r.default_branch,r.is_archived,r.verified_at,"
            "s.provider,s.conversation_id,s.message_id,s.conversation_url,"
            "s.conversation_title,s.first_seen_at "
            "FROM github_repository_refs r "
            "JOIN github_repository_ref_sources s ON s.canonical_url=r.canonical_url "
            "JOIN conversations c ON c.provider=s.provider AND c.conversation_id=s.conversation_id "
            "WHERE c.project_id=? ORDER BY s.first_seen_at DESC LIMIT 100",
            (project_id,),
        ).fetchall()
        artifact_rows = db.execute(
            "SELECT a.provider,a.conversation_id,a.artifact_id,a.language,"
            "a.content_fingerprint,c.title,c.source_fingerprint "
            "FROM code_artifacts a JOIN conversations c "
            "ON c.provider=a.provider AND c.conversation_id=a.conversation_id "
            "AND c.source_fingerprint=a.source_fingerprint "
            "WHERE c.project_id=? ORDER BY c.captured_at DESC LIMIT 200",
            (project_id,),
        ).fetchall()
        snapshot_rows = db.execute(
            "SELECT snapshot_id,repository_path,tree_fingerprint,file_count,"
            "language_summary_json,created_at FROM tree_snapshots "
            "WHERE project_id=? ORDER BY created_at DESC LIMIT ?",
            (project_id, snapshot_limit),
        ).fetchall()

    conversations = []
    for row in conversation_rows:
        conversations.append({
            "provider": row["provider"],
            "conversation_id": row["conversation_id"],
            "title": row["title"],
            "url": row["url"],
            "completeness": row["completeness"],
            "message_count": row["message_count"],
            "source_fingerprint": row["source_fingerprint"],
            "assignment_status": row["assignment_status"],
            "captured_at": row["captured_at"],
            "evidence_ref": f"{row['provider']}:{row['conversation_id']}",
        })

    repository_references = [
        {
            "url": row["canonical_url"],
            "owner": row["owner"],
            "repository": row["repository"],
            "verification_status": row["verification_status"],
            "html_url": row["html_url"],
            "description": row["description"],
            "default_branch": row["default_branch"],
            "is_archived": bool(row["is_archived"]) if row["is_archived"] is not None else None,
            "verified_at": row["verified_at"],
            "source": {
                "provider": row["provider"],
                "conversation_id": row["conversation_id"],
                "message_id": row["message_id"],
                "conversation_title": row["conversation_title"],
                "conversation_url": row["conversation_url"],
                "first_seen_at": row["first_seen_at"],
            },
        }
        for row in reference_rows
    ]
    code_artifacts = [
        {
            "provider": row["provider"],
            "conversation_id": row["conversation_id"],
            "artifact_id": row["artifact_id"],
            "language": row["language"],
            "content_fingerprint": row["content_fingerprint"],
            "conversation_title": row["title"],
            "source_fingerprint": row["source_fingerprint"],
            "verification_status": "candidate_not_repository_verified",
        }
        for row in artifact_rows
    ]

    snapshots = []
    for row in snapshot_rows:
        try:
            languages = json.loads(row["language_summary_json"] or "{}")
        except (TypeError, ValueError):
            languages = {}
        snapshots.append({
            "snapshot_id": row["snapshot_id"],
            "repository_path": row["repository_path"],
            "tree_fingerprint": row["tree_fingerprint"],
            "file_count": row["file_count"],
            "language_summary": languages if isinstance(languages, dict) else {},
            "created_at": row["created_at"],
        })

    latest_audit = None
    audit_dir = (vault.root / "projects" / project_id / "audits")
    try:
        resolved_dir = audit_dir.resolve(strict=True)
        if resolved_dir.is_relative_to(vault.root.resolve()) and resolved_dir.is_dir():
            candidates = sorted(
                (item for item in resolved_dir.glob("*.json") if item.is_file() and not item.is_symlink()),
                key=lambda item: item.stat().st_mtime,
                reverse=True,
            )
            for candidate in candidates[:10]:
                if candidate.stat().st_size > 2_000_000:
                    continue
                try:
                    payload = json.loads(candidate.read_text(encoding="utf-8"))
                except (OSError, UnicodeDecodeError, ValueError):
                    continue
                if payload.get("project_id") != project_id or not payload.get("audit_fingerprint"):
                    continue
                latest_audit = {
                    "audit_fingerprint": payload["audit_fingerprint"],
                    "snapshot_id": payload.get("snapshot_id"),
                    "tree_fingerprint": payload.get("tree_fingerprint"),
                    "generated_at": payload.get("generated_at"),
                    "files_inspected": payload.get("files_inspected", 0),
                    "files_skipped": payload.get("files_skipped", 0),
                    "summary": payload.get("summary", {}),
                    "findings": payload.get("findings", [])[:finding_limit],
                    "findings_total": len(payload.get("findings", [])),
                    "findings_truncated": len(payload.get("findings", [])) > finding_limit,
                    "report_ref": candidate.name,
                }
                break
    except (OSError, RuntimeError):
        latest_audit = None

    # Match the Vault's canonical local path to the durable Git inventory by
    # exact normalized path only. Similar names, origins and project groups are
    # intentionally not enough to claim repository identity.
    local_path = project.get("repository_path")
    local_matches: list[dict[str, Any]] = []
    if isinstance(local_path, str) and local_path.strip():
        try:
            project_path_key = os.path.normcase(str(Path(local_path).expanduser().resolve())).casefold()
        except (OSError, RuntimeError):
            project_path_key = ""
        if project_path_key:
            for item in repository_inventory or []:
                candidate_path = item.get("path")
                if not isinstance(candidate_path, str) or not candidate_path.strip():
                    continue
                try:
                    candidate_key = os.path.normcase(str(Path(candidate_path).expanduser().resolve())).casefold()
                except (OSError, RuntimeError):
                    continue
                if candidate_key != project_path_key:
                    continue
                local_matches.append({
                    "path": candidate_path,
                    "name": item.get("name"),
                    "branch": item.get("branch"),
                    "head_sha": item.get("head_sha"),
                    "working_tree_dirty": item.get("dirty"),
                    "scan_status": item.get("scan_status"),
                    "scan_error": item.get("scan_error"),
                    "last_seen_at": item.get("last_seen_at"),
                    "scan_count": item.get("scan_count"),
                    "tree_path": item.get("tree_path"),
                    "tree_sha256": item.get("tree_sha256"),
                    "tree_entries": item.get("tree_entries"),
                    "tree_truncated": item.get("tree_truncated"),
                    "tree_generated_at": item.get("tree_generated_at"),
                    "tree_error": item.get("tree_error"),
                    "evidence_source": "persistent_repository_learning_inventory",
                    "github_live": fetch_github_live_evidence(
                        str(item.get("origin") or ""), item.get("head_sha")
                    ),
                })
    local_inventory = {
        "match_status": "exact_path_match" if local_matches else "no_exact_path_match",
        "project_repository_path": local_path,
        "repositories": local_matches,
        "inventory_records_considered": len(repository_inventory or []),
        "note": (
            "Branch and commit are the last persisted repository-learning observation, not a live Git probe. "
            "No repository was inferred from a similar name, remote URL or project-group suggestion."
        ),
    }

    latest_capture = max((item["captured_at"] or "" for item in conversations), default=None) or None
    latest_snapshot = snapshots[0]["created_at"] if snapshots else None
    return {
        "schema": "dgm-mat.project-dossier.v1",
        "project": {
            "project_id": project["project_id"],
            "name": project["name"],
            "aliases": project.get("aliases", []),
            "repository_path": project.get("repository_path"),
        },
        "generated_from": "local_vault_read_only",
        "coverage": {
            "vault_conversations_total": total,
            "conversations_returned": len(conversations),
            "conversation_limit": conversation_limit,
            "by_provider": {row["provider"]: row["count"] for row in provider_rows},
            "by_completeness": {row["completeness"]: row["count"] for row in completeness_rows},
            "tree_snapshots_returned": len(snapshots),
            "provider_archive_completeness": "unknown",
            "note": "This reports only evidence currently assigned to this Vault project. It does not prove that all provider conversations or local repositories have been captured.",
        },
        "conversations": conversations,
        "repository": {
            "snapshots": snapshots,
            "conversation_linked_references": repository_references,
            "conversation_linked_code_candidates": code_artifacts,
            "latest_snapshot_at": latest_snapshot,
            "git_branch_and_commit": "available_only_when_exact_local_inventory_match_exists",
            "local_inventory": local_inventory,
        },
        "static_audit": latest_audit,
        "status": {
            "classification": "evidence_partial" if total or snapshots or latest_audit else "no_evidence",
            "latest_conversation_capture_at": latest_capture,
            "latest_repository_snapshot_at": latest_snapshot,
            "implementation_completion": "not_inferred",
            "operator_decisions": "not_inferred_from_conversation_text",
        },
        "limitations": [
            "No transcript bodies are returned by this endpoint.",
            "Conversation assignment is reported as stored; this endpoint does not infer project membership.",
            "AI proposals are not promoted to operator decisions.",
            "A repository snapshot is not proof of current Git branch, commit, runtime health or test status.",
            "Local Git metadata is a persisted repository-learning observation and may be stale; it is not a live Git probe.",
            "Local repository identity is linked only by exact normalized repository path; unmatched candidates are not inferred.",
            "Live GitHub metadata is a separate timestamped read-only observation; commit checks refer only to the exact persisted local HEAD SHA and may be unavailable or rate-limited.",
            "Provider archive completeness remains unknown unless separately verified by provider-specific capture evidence.",
        ],
        "read_only": True,
    }
