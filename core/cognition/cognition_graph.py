import networkx as nx
from typing import List, Dict, Any, Set
from core.cognition.cognition_models import CognitionNode, CognitionEdge, NodeCategory, EdgeType
from core.observability.logger import dgm_logger

class CognitionGraph:
    RESERVED_KEYS = {"category", "type", "id", "name"}

    def __init__(self):
        self.graph = nx.DiGraph()

    def sanitize_node_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Removes reserved keys from metadata to avoid conflicts during graph construction."""
        return {k: v for k, v in metadata.items() if k not in self.RESERVED_KEYS}

    def update(self, nodes: List[CognitionNode], edges: List[CognitionEdge]):
        """Defensively updates the graph with new nodes and edges."""
        for node in nodes:
            try:
                if not node.id:
                    dgm_logger.warning("CognitionGraph: Skipping node with missing ID.")
                    continue

                sanitized_meta = self.sanitize_node_metadata(node.metadata)

                # Check for node collisions
                if node.id in self.graph:
                    dgm_logger.info(f"CognitionGraph: Updating existing node {node.id}")

                self.graph.add_node(
                    node.id,
                    category=node.category,
                    original_metadata=node.metadata, # Preserve original
                    **sanitized_meta
                )
            except Exception as exc:
                dgm_logger.error(f"CognitionGraph: Failed to add node {node.id}: {exc}")

        for edge in edges:
            try:
                if edge.source not in self.graph or edge.target not in self.graph:
                    dgm_logger.warning(f"CognitionGraph: Skipping edge {edge.source}->{edge.target} due to missing node.")
                    continue

                # Check for duplicate relationships
                if self.graph.has_edge(edge.source, edge.target):
                    existing_type = self.graph[edge.source][edge.target].get('edge_type')
                    if existing_type == edge.edge_type:
                        dgm_logger.debug(f"CognitionGraph: Duplicate edge {edge.source}->{edge.target} of type {edge.edge_type}")
                        continue

                self.graph.add_edge(
                    edge.source,
                    edge.target,
                    edge_type=edge.edge_type,
                    **edge.metadata
                )
            except Exception as exc:
                dgm_logger.error(f"CognitionGraph: Failed to add edge {edge.source}->{edge.target}: {exc}")

    def validate_graph(self) -> Dict[str, Any]:
        """Performs strict validation of the graph structure."""
        report = {
            "cycles": list(nx.simple_cycles(self.graph)),
            "orphans": [n for n in self.graph.nodes if self.graph.degree(n) == 0],
            "invalid_edges": [] # Can be extended for specific dependency rules
        }

        if report["cycles"]:
            dgm_logger.warning(f"CognitionGraph: Recursive topology loops detected: {report['cycles']}")

        if report["orphans"]:
            dgm_logger.info(f"CognitionGraph: Orphan nodes detected: {report['orphans']}")

        return report

    def get_dependencies(self, node_id: str) -> List[str]:
        if node_id not in self.graph: return []
        return list(self.graph.successors(node_id))

    def get_dependents(self, node_id: str) -> List[str]:
        if node_id not in self.graph: return []
        return list(self.graph.predecessors(node_id))

    def find_cycles(self) -> List[List[str]]:
        return list(nx.simple_cycles(self.graph))

    def calculate_centrality(self) -> Dict[str, float]:
        try:
            return nx.degree_centrality(self.graph)
        except Exception:
            return {}

    def get_subgraph_by_category(self, category: NodeCategory):
        nodes = [n for n, d in self.graph.nodes(data=True) if d.get('category') == category]
        return self.graph.subgraph(nodes)
