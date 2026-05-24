from pathlib import Path
import json

class AttachmentClassifier:
    """
    Classifies uploaded files and routes them to appropriate contexts.
    """
    def classify(self, file_path: Path) -> str:
        suffix = file_path.suffix.lower()
        if suffix in ['.env']: return "config"
        if suffix in ['.zip', '.tar', '.gz']: return "archive"
        if suffix in ['.jpg', '.png', '.svg']: return "image"
        if suffix in ['.py', '.js', '.ts', '.go', '.rs']: return "source_code"
        if suffix in ['.md', '.txt']: return "documentation"
        if suffix in ['.log']: return "logs"
        return "unknown"
