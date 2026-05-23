from typing import List, Dict, Any
from core.cognition.cognition_models import CognitionNode, CognitionEdge, NodeCategory, EdgeType
from core.cognition.cognition_graph import CognitionGraph

class TopologyEngine:
    def __init__(self):
        self.graph = CognitionGraph()

    def build_topology(self, repos: List[Dict[str, Any]], agents: List[Dict[str, Any]], providers: List[Dict[str, Any]]) -> CognitionGraph:
        nodes = []
        edges = []

        for repo in repos:
            nodes.append(CognitionNode(
                id=repo['name'],
                category=NodeCategory.REPOSITORY,
                metadata=repo
            ))

        for agent in agents:
            nodes.append(CognitionNode(
                id=agent['id'],
                category=NodeCategory.AGENT,
                metadata=agent
            ))
            # Edge from agent to its repository if known
            if 'repo' in agent:
                edges.append(CognitionEdge(
                    source=agent['id'],
                    target=agent['repo'],
                    edge_type=EdgeType.OWNERSHIP
                ))

        for provider in providers:
            nodes.append(CognitionNode(
                id=provider['name'],
                category=NodeCategory.PROVIDER,
                metadata=provider
            ))

        self.graph.update(nodes, edges)
        return self.graph

    def get_topology_summary(self) -> Dict[str, Any]:
        return {
            "nodes_count": self.graph.graph.number_of_nodes(),
            "edges_count": self.graph.graph.number_of_edges(),
            "categories": [n[1]['category'] for n in self.graph.graph.nodes(data=True)]
        }
