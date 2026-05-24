from pathlib import Path
from typing import Dict, Any

class ProjectIdentity:
    """
    Identifies and categorizes projects based on their structure.
    """
    def __init__(self, name: str, path: Path, metadata: Dict[str, Any]):
        self.name = name
        self.path = path
        self.metadata = metadata

    @classmethod
    def identify(cls, path: Path) -> 'ProjectIdentity':
        name = path.name
        metadata = {
            "path": str(path),
            "tech_stack": cls._detect_tech_stack(path),
            "has_git": (path / ".git").exists()
        }
        return cls(name, path, metadata)

    @staticmethod
    def _detect_tech_stack(path: Path) -> list:
        stack = []
        if (path / "package.json").exists(): stack.append("nodejs")
        if (path / "requirements.txt").exists() or (path / "pyproject.toml").exists(): stack.append("python")
        if (path / "Cargo.toml").exists(): stack.append("rust")
        return stack
