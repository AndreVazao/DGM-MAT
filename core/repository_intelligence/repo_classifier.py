from pathlib import Path

def classify_repo(
    repo_path: Path,
    tech_stack: list[str],
) -> str:
    """
    Classifies a repository based on its name and tech stack.
    Follows DGM-MAT Strategic Architecture v1 rules and intake list priorities.
    """
    name = repo_path.name.lower()

    # 1. Specific Names from Intake List (Highest Priority)
    if any(k in name for k in ["n8n", "temporal", "langchain"]):
        return "core"
    if any(k in name for k in ["crewai", "autogen"]):
        return "agents"
    if any(k in name for k in ["gpt4free", "freedomgpt", "free-claude", "free-code"]):
        return "labs"
    if any(k in name for k in ["freqtrade"]):
        return "finance"
    if any(k in name for k in ["qdrant", "weaviate", "chroma"]):
        return "memory"
    if any(k in name for k in ["prometheus", "traefik"]):
        return "infra"
    if any(k in name for k in ["grafana", "coreui"]):
        return "ui"
    if any(k in name for k in ["freellmapi"]):
        return "providers"
    if any(k in name for k in ["aiclient2api", "kong"]):
        return "connectors"

    # 2. General Keywords
    # Financial / Trading
    if any(k in name for k in ["trad", "finance", "quant", "backtest", "market"]):
        return "finance"

    # Multi-Agent Systems
    if any(k in name for k in ["agent", "multi-agent", "autonomous"]):
        return "agents"

    # Vector Database / Memory
    if any(k in name for k in ["vector", "memory"]):
        return "memory"

    # Observability / Infrastructure
    if any(k in name for k in ["monitoring", "metrics", "infrastructure", "infra"]):
        return "infra"

    # UI / Dashboard
    if any(k in name for k in ["ui", "dashboard", "admin", "template", "frontend", "bootstrap"]):
        return "ui"

    # LLM Providers
    if any(k in name for k in ["provider", "openai", "anthropic", "gemini"]):
        return "providers"

    # AI Experimentation / LLM tools (LABS)
    if any(k in name for k in ["gpt", "claude", "llm", "ai", "experiment", "research", "lab"]):
        return "labs"

    # System Orchestration / Core
    if any(k in name for k in ["orchestrator", "engine", "core", "dgm-mat"]):
        return "core"

    # API Integration / Connectors
    if any(k in name for k in ["connector", "api", "bridge", "integration", "public-apis"]):
        return "connectors"

    # 3. Mobile (Legacy/Experimental)
    if "mobile" in name:
        return "product"

    # 4. Otherwise
    return "external-labs"
