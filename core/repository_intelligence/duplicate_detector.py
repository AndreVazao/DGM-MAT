from collections import defaultdict

from core.repository_intelligence.models import (
    RepositoryInfo,
)


class DuplicateDetector:

    def detect(
        self,
        repos: list[RepositoryInfo],
    ):

        grouped = defaultdict(list)

        for repo in repos:

            key = tuple(
                sorted(repo.tech_stack)
            )

            grouped[key].append(repo)

        duplicates = []

        for stack, items in grouped.items():

            if len(items) > 1:

                duplicates.append(
                    {
                        "stack": stack,
                        "repos": [
                            r.name
                            for r in items
                        ],
                    }
                )

        return duplicates
