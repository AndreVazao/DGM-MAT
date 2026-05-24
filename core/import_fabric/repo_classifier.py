from pathlib import Path
from typing import List, Dict, Any
from core.repository_intelligence.repo_classifier import classify_repo as legacy_classify
from core.repository_intelligence.tech_detector import detect_tech_stack

class RepoClassifier:
    """
    Classifies imported repositories based on their structure and technology stack.
    """
    def classify(self, repo_path: Path) -> str:
        tech_stack = detect_tech_stack(repo_path)
        # Reuse existing legacy classifier for now as per rules (Reuse existing systems)
        role = legacy_classify(repo_path, tech_stack)
        return role
