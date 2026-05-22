from pathlib import Path


def classify_repo(
    repo_path: Path,
    tech_stack: list[str],
) -> str:

    name = repo_path.name.lower()
    tech_stack_lower = [t.lower() for t in tech_stack]

    if "mobile" in name:
        return "mobile"

    if "plugin" in name:
        return "plugins"

    if "provider" in name:
        return "providers"

    if "lab" in name:
        return "labs"

    if "deploy" in name:
        return "deployment"

    if "connector" in name:
        return "connectors"

    if "python" in tech_stack_lower:
        return "backend"

    return "general"
