import sys
import os
import json
from pathlib import Path

# Ensure local imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.repository_intelligence.repo_importer import RepoImporter
from core.observability.logger import dgm_logger

DEFAULT_REPOS = [
    "https://github.com/xtekky/gpt4free",
    "https://github.com/FreeCAD/FreeCAD",
    "https://github.com/justlovemaki/AIClient2API",
    "https://github.com/public-apis/public-apis",
    "https://github.com/Alishahryar1/free-claude-code",
    "https://github.com/paoloanzn/free-code",
    "https://github.com/ohmplatform/FreedomGPT",
    "https://github.com/coreui/coreui-free-bootstrap-admin-template",
    "https://github.com/freqtrade/freqtrade",
    "https://github.com/tashfeenahmed/freellmapi"
]

def main():
    importer = RepoImporter()

    urls = sys.argv[1:] if len(sys.argv) > 1 else DEFAULT_REPOS

    results = []
    dgm_logger.info(f"Starting bulk import of {len(urls)} repositories...")

    for url in urls:
        try:
            res = importer.import_repo(url)
            results.append(res)
            print(f"✅ Imported {res['repo_name']} as {res['classification']}")
        except Exception as e:
            dgm_logger.error(f"Failed to import {url}: {e}")
            results.append({"url": url, "status": "error", "message": str(e)})

    # Output summary
    print("\n" + "="*30)
    print("IMPORT SUMMARY")
    print("="*30)
    for r in results:
        if r.get("status") == "imported":
            print(f"- {r['repo_name']}: {r['classification']} ({r['path']})")
        else:
            print(f"- ERROR: {r.get('url') or r.get('repo_name')} - {r.get('message')}")

if __name__ == "__main__":
    main()
