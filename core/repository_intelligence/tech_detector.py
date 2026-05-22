from pathlib import Path


def detect_tech_stack(
    repo_path: Path,
) -> list[str]:

    detected = []

    if (
        repo_path / "package.json"
    ).exists():

        detected.append("Node.js")

    if (
        repo_path / "requirements.txt"
    ).exists():

        detected.append("Python")

    if (
        repo_path / "pyproject.toml"
    ).exists():

        detected.append("Python")

    if (
        repo_path / "Cargo.toml"
    ).exists():

        detected.append("Rust")

    if (
        repo_path / "go.mod"
    ).exists():

        detected.append("Go")

    if (
        repo_path / "docker-compose.yml"
    ).exists():

        detected.append("Docker")

    return detected
