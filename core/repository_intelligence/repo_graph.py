import networkx as nx

from core.repository_intelligence.models import (
    RepositoryInfo,
)


class RepositoryGraph:

    def build(
        self,
        repos: list[RepositoryInfo],
    ):

        graph = nx.Graph()

        for repo in repos:

            graph.add_node(
                repo.name,
                category=repo.category,
            )

        for repo in repos:

            for other in repos:

                if repo == other:
                    continue

                common = set(
                    repo.tech_stack
                ).intersection(
                    other.tech_stack
                )

                if common:

                    graph.add_edge(
                        repo.name,
                        other.name,
                        weight=len(common),
                    )

        return graph
