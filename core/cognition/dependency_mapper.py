from typing import List, Dict, Any
import os
import json
from core.cognition.cognition_models import CognitionNode, CognitionEdge, NodeCategory, EdgeType

class DependencyMapper:
    def map_dependencies(self, root_path: str) -> List[CognitionEdge]:
        edges = []
        # Support Python (requirements.txt), Node.js (package.json)
        for root, dirs, files in os.walk(root_path):
            if 'package.json' in files:
                edges.extend(self._parse_package_json(os.path.join(root, 'package.json')))
            if 'requirements.txt' in files:
                edges.extend(self._parse_requirements_txt(os.path.join(root, 'requirements.txt')))
        return edges

    def _parse_package_json(self, path: str) -> List[CognitionEdge]:
        edges = []
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                deps = data.get('dependencies', {})
                dev_deps = data.get('devDependencies', {})
                repo_name = os.path.basename(os.path.dirname(path))
                for dep in {**deps, **dev_deps}:
                    edges.append(CognitionEdge(
                        source=repo_name,
                        target=dep,
                        edge_type=EdgeType.DEPENDENCY,
                        metadata={"manager": "npm"}
                    ))
        except Exception:
            pass  # nosec: B110
        return edges

    def _parse_requirements_txt(self, path: str) -> List[CognitionEdge]:
        edges = []
        try:
            repo_name = os.path.basename(os.path.dirname(path))
            with open(path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        dep = line.split('==')[0].split('>=')[0].strip()
                        edges.append(CognitionEdge(
                            source=repo_name,
                            target=dep,
                            edge_type=EdgeType.DEPENDENCY,
                            metadata={"manager": "pip"}
                        ))
        except Exception:
            pass  # nosec: B110
        return edges
