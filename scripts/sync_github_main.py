#!/usr/bin/env python3
"""Run the fixed, approval-gated DGM-MAT GitHub-main isolated sync.

This command never updates the authoritative checkout. It fetches origin/main
and creates or verifies one dedicated detached worktree.
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from core.autonomy.github_worktree_sync import GitHubWorktreeSync


def main() -> int:
    default_root = os.getenv("DGM_MAT_REPOSITORY_ROOT")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(default_root) if default_root else Path(__file__).resolve().parents[1],
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "reports" / "diagnostics",
    )
    args = parser.parse_args()

    result = GitHubWorktreeSync(args.repo_root).sync()
    report = {
        "schema": "dgm-mat-github-self-sync.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "result": result,
    }
    args.report_dir.mkdir(parents=True, exist_ok=True)
    report_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    report_path = args.report_dir / f"DGM-MAT-GITHUB-SELF-SYNC-{report_date}.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": result["status"],
        "remote_sha": result["remote_sha"],
        "worktree_sha": result["worktree_sha"],
        "worktree_path": result["worktree_path"],
        "worktree_clean": result["worktree_clean"],
        "authoritative_head_unchanged": result["authoritative_head_unchanged"],
        "authoritative_worktree_unchanged": result["authoritative_worktree_unchanged"],
        "report": str(report_path),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
