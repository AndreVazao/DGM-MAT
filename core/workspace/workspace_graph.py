import networkx as nx
from typing import Dict, Any, List

class WorkspaceGraph:
    """
    Represents relationships between projects, repositories, and files.
    """
    def __init__(self):
        self.graph = nx.DiGraph()

    def add_project(self, identity):
        self.graph.add_node(identity.name, type="project", **identity.metadata)

    def add_relationship(self, source: str, target: str, rel_type: str):
        self.graph.add_edge(source, target, relation=rel_type)

    def get_context(self, project_name: str) -> Dict[str, Any]:
        if project_name not in self.graph:
            return {}

        related = list(self.graph.neighbors(project_name))
        return {
            "project": project_name,
            "related_nodes": related,
            "metadata": self.graph.nodes[project_name]
        }
