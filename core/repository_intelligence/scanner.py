from pathlib import Path

from core.repository_intelligence.models import (
    RepositoryInfo,
)

from core.repository_intelligence.tech_detector import (
    detect_tech_stack,
)

from core.repository_intelligence.repo_classifier import (
    classify_repo,
)


REPOS_ROOT = Path(
    "C:/Programas GodMode"
)


class RepositoryScanner:

    def scan(self) -> list[RepositoryInfo]:

        repositories = []

        if not REPOS_ROOT.exists():

            return repositories

        for item in REPOS_ROOT.iterdir():

            if not item.is_dir():
                continue

            has_git = (
                item / ".git"
            ).exists()

            tech_stack = detect_tech_stack(
                item
            )

            category = classify_repo(
                item,
                tech_stack,
            )

            total_files = sum(
                1
                for f in item.rglob("*")
                if f.is_file()
            )

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

        return repositories
