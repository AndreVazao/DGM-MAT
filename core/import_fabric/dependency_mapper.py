from pathlib import Path
from typing import List, Dict, Any
from core.repository_intelligence.tech_detector import detect_tech_stack

class DependencyMapper:
    """
    Maps dependencies of an imported repository.
    """
    def map_dependencies(self, repo_path: Path) -> List[str]:
        # Reuse existing tech detector
        return detect_tech_stack(repo_path)
