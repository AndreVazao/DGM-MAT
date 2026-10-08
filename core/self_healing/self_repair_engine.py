from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from core.observability.logger import dgm_logger
from core.repository_intelligence.portfolio_auditor import RepositoryAuditEngine


@dataclass
class RepairAction:
    id: str
    category: str
    risk: str
    description: str
    allowed_automatically: bool
    command: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SelfRepairEngine:
    """Controlled self-repair for DGM-MAT.

    The engine separates diagnosis from mutation. Safe automatic actions are
    deliberately narrow; structural repository moves, deletes, renames,
    commits and pushes always remain approval-gated.
    """

    def __init__(self, repo_root: Path | str | None = None):
        self.repo_root = Path(repo_root or Path(__file__).resolve().parents[2])
        self.auditor = RepositoryAuditEngine(self.repo_root.parent)

    def diagnose(self) -> dict[str, Any]:
        audit = self.auditor.audit_repository(self.repo_root)
        actions = self._plan(audit)
        return {
            "schema": "dgm-mat.self-repair.v1",
            "repository": audit.to_dict(),
            "actions": [a.to_dict() for a in actions],
            "automatic_actions": [a.to_dict() for a in actions if a.allowed_automatically],
            "approval_required": [a.to_dict() for a in actions if not a.allowed_automatically],
        }

    def apply_safe(self, *, dry_run: bool = True) -> dict[str, Any]:
        diagnosis = self.diagnose()
        applied: list[dict[str, Any]] = []
        skipped: list[dict[str, Any]] = []
        for action in diagnosis["actions"]:
            if not action["allowed_automatically"]:
                skipped.append(action)
                continue
            if dry_run:
                applied.append({**action, "status": "planned"})
                continue
            result = self._run_safe_action(action)
            applied.append({**action, **result})
        return {
            "schema": "dgm-mat.self-repair-result.v1",
            "dry_run": dry_run,
            "applied": applied,
            "skipped_for_approval": skipped,
        }

    def _plan(self, audit) -> list[RepairAction]:
        actions: list[RepairAction] = []
        if audit.missing_readme if hasattr(audit, "missing_readme") else False:
            actions.append(
                RepairAction(
                    id="README-001",
                    category="documentation",
                    risk="LOW",
                    description="Create a minimal truthful README from observed repository metadata.",
                    allowed_automatically=False,
                )
            )
        if not audit.origin:
            actions.append(
                RepairAction(
                    id="REMOTE-001",
                    category="governance",
                    risk="MEDIUM",
                    description="Determine repository authority and configure an origin.",
                    allowed_automatically=False,
                )
            )
        if audit.dirty:
            actions.append(
                RepairAction(
                    id="GIT-001",
                    category="safety",
                    risk="HIGH",
                    description="Working tree is dirty; preserve local changes before structural repair.",
                    allowed_automatically=False,
                )
            )
        if audit.name == "DGM-MAT":
            actions.append(
                RepairAction(
                    id="SELF-001",
                    category="self-test",
                    risk="LOW",
                    description="Run the bounded DGM-MAT import/runtime smoke validation.",
                    allowed_automatically=True,
                )
            )
        return actions

    def _run_safe_action(self, action: dict[str, Any]) -> dict[str, Any]:
        if action["id"] == "SELF-001":
            command = ["python", "-c", "from core.bootstrap.runtime.bootstrap_engine import BootstrapEngine; c=BootstrapEngine('HEADLESS').prepare(); print(c.runtime_state)"]
            try:
                result = subprocess.run(
                    command,
                    cwd=str(self.repo_root),
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False,
                )
                ok = result.returncode == 0 and "prepared" in result.stdout
                return {
                    "status": "passed" if ok else "failed",
                    "returncode": result.returncode,
                    "stdout_tail": result.stdout[-2000:],
                    "stderr_tail": result.stderr[-2000:],
                }
            except Exception as exc:
                dgm_logger.error(f"SelfRepairEngine: self-test failed: {exc}")
                return {"status": "failed", "error": str(exc)}
        return {"status": "not-implemented"}
