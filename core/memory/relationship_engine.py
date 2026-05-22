import networkx as nx

from core.repository_intelligence.models import (
    RepositoryInfo,
)


class RelationshipEngine:

    def build_relationships(
        self,
        repos: list[RepositoryInfo],
    ):

        graph = nx.Graph()

        for repo in repos:

            graph.add_node(
                repo.name,
                type="repository",
            )

        for repo in repos:

            for other in repos:

                if repo == other:
                    continue

                shared = set(
                    repo.tech_stack
                ).intersection(
                    other.tech_stack
                )

                if shared:

                    graph.add_edge(
                        repo.name,
                        other.name,
                        relation="shared_stack",
                    )

        return graph
