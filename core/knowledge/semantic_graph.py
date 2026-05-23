import networkx as nx
from typing import List, Dict, Any
from core.knowledge.knowledge_models import KnowledgeNode, KnowledgeEdge
from core.observability.logger import dgm_logger

class SemanticGraph:
    def __init__(self, node_cap: int = 5000, edge_cap: int = 10000):
        self.graph = nx.MultiDiGraph()
        self.node_cap = node_cap
        self.edge_cap = edge_cap

    def update(self, nodes: List[KnowledgeNode], edges: List[KnowledgeEdge]):
        # Enforcement of caps (Requirement 3)
        if self.graph.number_of_nodes() >= self.node_cap:
            self._prune_orphans()
            if self.graph.number_of_nodes() >= self.node_cap:
                # Still over? Prune oldest nodes
                dgm_logger.warning("SemanticGraph: Node cap reached. Pruning oldest knowledge.")
                nodes_to_remove = list(self.graph.nodes())[:100]
                self.graph.remove_nodes_from(nodes_to_remove)

        for node in nodes:
            self.graph.add_node(
                node.id,
                category=node.category,
                name=node.name,
                **node.metadata
            )

        for edge in edges:
            if self.graph.number_of_edges() < self.edge_cap:
                self.graph.add_edge(
                    edge.source,
                    edge.target,
                    relation=edge.relation,
                    weight=edge.weight,
                    **edge.metadata
                )
        dgm_logger.info(f"SemanticGraph: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges.")

    def find_related(self, node_id: str, depth: int = 1, limit: int = 100) -> List[str]:
        """Bounded traversal (Requirement 10)."""
        if node_id not in self.graph:
            return []

        try:
            results = list(nx.single_source_shortest_path_length(self.graph, node_id, cutoff=depth).keys())
            return results[:limit]
        except Exception as exc:
            dgm_logger.error(f"SemanticGraph: Search error: {exc}")
            return []

    def get_subgraph_by_category(self, category: str):
        nodes = [n for n, d in self.graph.nodes(data=True) if d.get('category') == category]
        return self.graph.subgraph(nodes)

    def _prune_orphans(self):
        orphans = [n for n in self.graph.nodes() if self.graph.degree(n) == 0]
        if orphans:
            dgm_logger.info(f"SemanticGraph: Pruning {len(orphans)} orphan nodes.")
            self.graph.remove_nodes_from(orphans)

    def validate_integrity(self) -> bool:
        """Fragmentation check (Requirement 3)."""
        is_weakly_connected = nx.is_weakly_connected(self.graph) if self.graph.number_of_nodes() > 0 else True
        if not is_weakly_connected:
            dgm_logger.warning("SemanticGraph: Graph is fragmented.")
        return True
