import sys
from pathlib import Path
from core.workspace.workspace_graph import WorkspaceGraph
from core.operator.capability_extractor import CapabilityExtractor
from core.observability.logger import dgm_logger

def validate():
    dgm_logger.info("Validating Repo Import & Capability Extraction...")
    graph = WorkspaceGraph()
    extractor = CapabilityExtractor(graph)

    # Simulate a repo analysis
    repo_path = Path("labs/external/langgraph")
    repo_path.mkdir(parents=True, exist_ok=True)
    (repo_path / "main.py").touch()

    caps = extractor.analyze_repo(repo_path)
    if "orchestration" in caps["patterns"]:
        dgm_logger.info("CapabilityExtractor: SUCCESS")
    else:
        dgm_logger.error("CapabilityExtractor: FAILED")
        return False

    return True

if __name__ == "__main__":
    if validate():
        print("REPO IMPORT VALIDATION: PASSED")
    else:
        print("REPO IMPORT VALIDATION: FAILED")
        sys.exit(1)
