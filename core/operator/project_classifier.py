from pathlib import Path
from core.repository_intelligence.repo_classifier import classify_repo

class ProjectClassifier:
    """
    Classifies projects within the workspace.
    """
    def classify_project(self, project_path: Path) -> str:
        # Reuse existing classifier
        return classify_repo(project_path, [])
