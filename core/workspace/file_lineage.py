from pathlib import Path

class FileLineage:
    """
    Tracks the origin and evolution of files across projects.
    """
    def __init__(self):
        self.lineage = {}

    def record_origin(self, file_path: Path, origin_context: str):
        self.lineage[str(file_path)] = {
            "origin": origin_context,
            "created_at": Path(file_path).stat().st_ctime if Path(file_path).exists() else None
        }
