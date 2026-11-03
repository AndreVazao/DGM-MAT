#!/usr/bin/env python3
"""Inventory local AI conversation sources without reading credentials or transcripts."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from core.recovery.ai_source_inventory import (
    inventory_local_ai_sources,
    prepare_recovery_inbox,
    write_inventory_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=100, help="Maximum conversation route metadata entries per provider (1-500).")
    parser.add_argument("--output", type=Path, help="Private JSON report path; omitted means stdout only.")
    parser.add_argument("--prepare-inbox", action="store_true", help="Create provider export intake folders without overwriting existing files.")
    parser.add_argument("--inbox-root", type=Path, help="Optional intake root; defaults to %LOCALAPPDATA%/DGM-MAT/recovery-inbox.")
    args = parser.parse_args()

    report = inventory_local_ai_sources(limit=args.limit)
    if args.prepare_inbox:
        report["recovery_inbox"] = prepare_recovery_inbox(args.inbox_root)
    if args.output:
        destination = write_inventory_report(report, args.output)
        summary = {
            "status": "completed",
            "report_path": str(destination),
            "profiles": [],
            "conversation_content_read": False,
            "cookies_or_tokens_read": False,
            "complete_conversation_inventory": False,
        }
        for profile in report["profiles"]:
            history = profile["history"]
            summary["profiles"].append({
                "profile_name": profile["profile_name"],
                "history_status": history["status"],
                "url_rows_by_provider": history["url_rows_by_provider"],
                "unique_conversations_by_provider": history["conversation_routes_by_provider"],
            })
        if "recovery_inbox" in report:
            summary["recovery_inbox"] = report["recovery_inbox"]
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
