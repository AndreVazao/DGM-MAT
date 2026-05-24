class ProjectHealth:
    """
    Evaluates the health and maintenance status of projects.
    """
    def check_health(self, project_path) -> dict:
        return {
            "status": "active",
            "has_tests": (project_path / "tests").exists(),
            "has_docs": (project_path / "docs").exists() or (project_path / "README.md").exists()
        }
