import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from core.repository_intelligence.repo_importer import RepoImporter
from core.observability.logger import dgm_logger

MANDATORY_REPOS = [
    "https://github.com/agno-ai/agno", # agno (formerly OpenClaw/Phidata)
    "https://github.com/langchain-ai/langgraph",
    "https://github.com/stanfordnlp/dspy",
    "https://github.com/crewAIInc/crewAI",
    "https://github.com/assafelovic/gpt-researcher",
    "https://github.com/chroma-core/chroma",
    "https://github.com/ollama/ollama",
    "https://github.com/open-webui/open-webui",
    "https://github.com/temporalio/temporal",
    "https://github.com/copilotkit/copilotkit",
    "https://github.com/mendableai/firecrawl",
    "https://github.com/jxnl/instructor",
    "https://github.com/langgenius/dify",
    "https://github.com/pydantic/pydantic-ai",
    "https://github.com/n8n-io/n8n",
    "https://github.com/langflow-ai/langflow"
]

def run_phase35_imports():
    dgm_logger.info("Starting Phase 35 Mandatory Repository Imports...")
    importer = RepoImporter(workspace_path=Path("labs/external"))

    for repo_url in MANDATORY_REPOS:
        try:
            dgm_logger.info(f"Importing {repo_url}...")
            # Using category_override='LABS' as specified in Phase 35 objective
            result = importer.import_repo(repo_url, category_override="labs")
            dgm_logger.info(f"Successfully imported {result.get('repo_name')} to {result.get('path')}")
        except Exception as e:
            dgm_logger.error(f"Failed to import {repo_url}: {e}")

if __name__ == "__main__":
    run_phase35_imports()
