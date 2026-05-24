from pathlib import Path

def classify_repo(
    repo_path: Path,
    tech_stack: list[str],
) -> str:
    """
    Classifies a repository based on its name and tech stack.
    Follows DGM-MAT Strategic Architecture v1 rules.
    """
    name = repo_path.name.lower()

    # 1. Financial / Trading
    if any(k in name for k in ["trad", "finance", "quant", "backtest", "market"]):
        return "finance"

    # 2. UI / Dashboard
    if any(k in name for k in ["ui", "dashboard", "admin", "template", "frontend", "bootstrap"]):
        return "ui"

    # 3. LLM Providers
    if any(k in name for k in ["provider", "openai", "anthropic", "gemini"]):
        return "providers"

    # 4. AI Experimentation / LLM tools (Higher priority than Connectors for these keywords)
    if any(k in name for k in ["gpt", "claude", "llm", "ai", "experiment", "research", "lab"]):
        return "labs"

    # 5. API Integration / Connectors
    if any(k in name for k in ["connector", "api", "bridge", "integration", "public-apis"]):
        return "connectors"

    # 6. System Orchestration / Core
    if any(k in name for k in ["core", "orchestrator", "engine", "dgm-mat"]):
        return "core"

    # 7. Mobile (Legacy/Experimental)
    if "mobile" in name:
        return "product" # Map to product role or keep as product if it was 'mobile' before

    # 8. Otherwise
    return "external-labs"
