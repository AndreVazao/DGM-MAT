import os
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

class RepoIndexer:
    """
    Indexes the contents of an imported repository.
    """
    def index(self, repo_path: Path) -> Dict[str, Any]:
        index_data = {
            "path": str(repo_path),
            "files": [],
            "indexed_at": datetime.now().isoformat()
        }

        for root, dirs, files in os.walk(repo_path):
            if ".git" in dirs:
                dirs.remove(".git")

            for file in files:
                file_path = Path(root) / file
                relative_path = file_path.relative_to(repo_path)
                index_data["files"].append({
                    "path": str(relative_path),
                    "size": file_path.stat().st_size,
                    "extension": file_path.suffix
                })

        # Save index to dgm-meta.json or a separate file
        meta_path = repo_path / "dgm-meta.json"
        if meta_path.exists():
            with open(meta_path, "r") as f:
                meta = json.load(f)
            meta["index"] = index_data
            with open(meta_path, "w") as f:
                json.dump(meta, f, indent=2)

        return index_data
