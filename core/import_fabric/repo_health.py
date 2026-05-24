from pathlib import Path
from typing import Dict, Any

class RepoHealth:
    """
    Analyzes the health and structure of an imported repository.
    """
    def check_health(self, repo_path: Path) -> Dict[str, Any]:
        has_readme = (repo_path / "README.md").exists() or (repo_path / "readme.md").exists()
        has_tests = (repo_path / "tests").exists() or (repo_path / "test").exists()
        has_license = any(repo_path.glob("LICENSE*"))

        score = 0
        if has_readme: score += 40
        if has_tests: score += 40
        if has_license: score += 20

        return {
            "score": score / 100.0,
            "has_readme": has_readme,
            "has_tests": has_tests,
            "has_license": has_license
        }
