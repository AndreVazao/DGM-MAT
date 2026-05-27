import os
from pathlib import Path
from core.repository_intelligence.models import RepositoryInfo
from core.repository_intelligence.tech_detector import detect_tech_stack
from core.repository_intelligence.repo_classifier import classify_repo
from core.observability.logger import dgm_logger

# REPOS_ROOT now defaults to the canonical workspace (PHASE 42.1)
REPOS_ROOT = Path(os.getenv("DGM_REPOS_ROOT", "C:/ProgramasGodMode"))

class RepositoryScanner:
    def __init__(self, root_path: Path = REPOS_ROOT):
        self.root = root_path
        self.exclusions = {".runtime", ".git", "__pycache__", "node_modules", "dist", "build", ".venv"}

    def scan(self) -> list[RepositoryInfo]:
        repositories = []

        if not self.root.exists():
            dgm_logger.warning(f"RepositoryScanner: Root path {self.root} does not exist.")
            return repositories

        try:
            for item in self.root.iterdir():
                try:
                    if not item.is_dir():
                        continue

                    if item.name in self.exclusions:
                        continue

                    has_git = (item / ".git").exists()
                    tech_stack = detect_tech_stack(item)
                    category = classify_repo(item, tech_stack)

                    # Safe file counting with permission error handling
                    total_files = 0
                    try:
                        for f in item.rglob("*"):
                            try:
                                if f.is_file():
                                    if not any(part in self.exclusions for part in f.parts):
                                        total_files += 1
                            except (PermissionError, OSError):
                                continue
                    except (PermissionError, OSError):
                         dgm_logger.warning(f"RepositoryScanner: Access denied to some files in {item}")

                    repositories.append(
                        RepositoryInfo(
                            name=item.name,
                            path=item,
                            tech_stack=tech_stack,
                            total_files=total_files,
                            has_git=has_git,
                            category=category,
                        )
                    )
                except (PermissionError, OSError) as e:
                    dgm_logger.warning(f"RepositoryScanner: Error accessing {item}: {e}")
                    continue
        except Exception as e:
            dgm_logger.error(f"RepositoryScanner: Fatal error during scan: {e}")

        return repositories
