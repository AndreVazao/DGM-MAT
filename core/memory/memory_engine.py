from core.repository_intelligence.scanner import (
    RepositoryScanner,
)

from core.memory.project_families import (
    ProjectFamilies,
)

from core.memory.relationship_engine import (
    RelationshipEngine,
)

from core.memory.context_snapshot import (
    ContextSnapshot,
)


class MemoryEngine:

    def run(self):

        scanner = RepositoryScanner()

        repos = scanner.scan()

        families = (
            ProjectFamilies()
            .build(repos)
        )

        relationships = (
            RelationshipEngine()
            .build_relationships(repos)
        )

        snapshot_content = []

        snapshot_content.append(
            "PROJECT FAMILIES"
        )

        for root, items in families.items():

            snapshot_content.append(
                f"{root}: {items}"
            )

        snapshot_content.append(
            "\nRELATIONSHIPS"
        )

        for edge in relationships.edges():

            snapshot_content.append(
                f"{edge[0]} <-> {edge[1]}"
            )

        ContextSnapshot().create(
            "\n".join(snapshot_content),
            tags=[
                "ecosystem",
                "relationships",
                "repos",
            ],
        )
