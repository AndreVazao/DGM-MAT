from pathlib import Path
from typing import List, Dict, Any

class WorkspaceMapper:
    """
    Maps the workspace structure and identifies project families.
    """
    def map_workspace(self, root: Path) -> Dict[str, Any]:
        return {
            "root": str(root),
            "projects": [d.name for d in root.iterdir() if d.is_dir()]
        }
