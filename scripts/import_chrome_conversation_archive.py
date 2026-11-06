from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.conversation_intelligence.chrome_archive_importer import ChromeConversationArchiveImporter


def main() -> int:
    parser = argparse.ArgumentParser(description="Import DGM-MAT Chrome conversation archive JSON files.")
    parser.add_argument("--inbox", help="Chrome downloads inbox directory.")
    parser.add_argument("--archive", help="Durable local archive directory.")
    args = parser.parse_args()
    result = ChromeConversationArchiveImporter(args.inbox, args.archive).import_inbox()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") in {"completed", "inbox_missing"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
