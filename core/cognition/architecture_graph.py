import json
import networkx as nx
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from core.cognition.cognition_graph import CognitionGraph
from core.cognition.cognition_models import CognitionNode, CognitionEdge, NodeCategory, EdgeType
from core.storage.storage_manager import storage_manager
from core.observability.logger import dgm_logger

class ArchitectureGraph(CognitionGraph):
    """
    Builds and manages internal graph relationships between modules, repos,
    dependencies, and execution flows.
    """
    def __init__(self):
        super().__init__()
        self.storage = storage_manager
        self.graph_filename = "architecture_graph_state.json"
        self._load_state()

    def _load_state(self):
        content = self.storage.read_data("graphs", self.graph_filename)
        if content:
            try:
                data = json.loads(content)
                nodes = [CognitionNode(**n) for n in data.get("nodes", [])]
                edges = [CognitionEdge(**e) for e in data.get("edges", [])]
                self.update(nodes, edges)
                dgm_logger.info(f"ArchitectureGraph: Loaded state with {len(nodes)} nodes and {len(edges)} edges.")
            except Exception as e:
                dgm_logger.error(f"ArchitectureGraph: Failed to load state: {e}")

    def save_state(self):
        nodes = []
        for n_id, data in self.graph.nodes(data=True):
            nodes.append({
                "id": n_id,
                "category": data.get("category"),
                "metadata": data.get("original_metadata", {})
            })

        edges = []
        for u, v, data in self.graph.edges(data=True):
            edges.append({
                "source": u,
                "target": v,
                "edge_type": data.get("edge_type"),
                "metadata": {k: v for k, v in data.items() if k != "edge_type"}
            })

        state = {"nodes": nodes, "edges": edges, "last_updated": datetime.now().isoformat()}
        self.storage.save_data("graphs", self.graph_filename, json.dumps(state, indent=2))
        dgm_logger.info("ArchitectureGraph: State saved successfully.")

    def map_module_relationships(self, repo_name: str, modules: List[Dict[str, Any]]):
        """Maps relationships between modules within a repository."""
        nodes = []
        edges = []

        # Add repository node
        nodes.append(CognitionNode(id=repo_name, category=NodeCategory.REPOSITORY))

        # Pre-pass to add all module nodes first to avoid missing node errors during edge creation
        for mod in modules:
            mod_id = f"{repo_name}.{mod['name']}"
            nodes.append(CognitionNode(id=mod_id, category=NodeCategory.WORKFLOW, metadata=mod))

            for dep in mod.get("dependencies", []):
                dep_id = f"{repo_name}.{dep}" if "." not in dep else dep
                nodes.append(CognitionNode(id=dep_id, category=NodeCategory.WORKFLOW))

        self.update(nodes, []) # Add all nodes first

        for mod in modules:
            mod_id = f"{repo_name}.{mod['name']}"
            edges.append(CognitionEdge(source=repo_name, target=mod_id, edge_type=EdgeType.OWNERSHIP))

            for dep in mod.get("dependencies", []):
                dep_id = f"{repo_name}.{dep}" if "." not in dep else dep
                edges.append(CognitionEdge(source=mod_id, target=dep_id, edge_type=EdgeType.DEPENDENCY))

        self.update([], edges) # Add all edges
        self.save_state()

    def detect_overlaps(self) -> List[Dict[str, Any]]:
        """Identifies duplicated capabilities or high similarity between branches in the graph."""
        overlaps = []
        nodes = list(self.graph.nodes(data=True))
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                n1_id, n1_data = nodes[i]
                n2_id, n2_data = nodes[j]

                if n1_data.get("category") == n2_data.get("category"):
                    if n1_id.split(".")[-1] == n2_id.split(".")[-1]:
                        overlaps.append({
                            "type": "Duplicate Capability",
                            "nodes": [n1_id, n2_id],
                            "category": n1_data.get("category")
                        })
        return overlaps

    def detect_orphans(self) -> List[str]:
        """Identifies nodes without any inbound or outbound edges."""
        validation = self.validate_graph()
        return validation.get("orphans", [])

    def traverse_dependencies(self, node_id: str, depth: int = 3) -> List[str]:
        """Performs a dependency traversal up to a certain depth."""
        if node_id not in self.graph:
            return []

        dependencies = set()
        to_visit = [(node_id, 0)]

        while to_visit:
            current, current_depth = to_visit.pop(0)
            if current_depth >= depth:
                continue

            for neighbor in self.graph.successors(current):
                if neighbor not in dependencies:
                    dependencies.add(neighbor)
                    to_visit.append((neighbor, current_depth + 1))

        return list(dependencies)

# Singleton instance
architecture_graph = ArchitectureGraph()
