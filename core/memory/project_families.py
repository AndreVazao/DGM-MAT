from collections import defaultdict

from core.repository_intelligence.models import (
    RepositoryInfo,
)

from core.memory.repo_similarity import (
    similarity,
)


class ProjectFamilies:

    def build(
        self,
        repos: list[RepositoryInfo],
    ):

        families = defaultdict(list)

        assigned = set()

        for repo in repos:

            if repo.name in assigned:
                continue

            family = [repo.name]

            assigned.add(repo.name)

            for other in repos:

                if other.name == repo.name:
                    continue

                score = similarity(
                    repo.name,
                    other.name,
                )

                if score > 0.55:

                    family.append(
                        other.name
                    )

                    assigned.add(
                        other.name
                    )

            families[repo.name] = family

        return families
