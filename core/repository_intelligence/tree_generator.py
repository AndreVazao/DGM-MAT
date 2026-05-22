from pathlib import Path


IGNORE = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "dist",
    "build",
}


def build_tree(
    path: Path,
    indent: str = "",
) -> str:

    lines = []

    items = sorted(
        path.iterdir(),
        key=lambda p: (
            not p.is_dir(),
            p.name.lower(),
        ),
    )

    for item in items:

        if item.name in IGNORE:
            continue

        lines.append(
            f"{indent}- {item.name}"
        )

        if item.is_dir():

            lines.extend(
                build_tree(
                    item,
                    indent + "  ",
                ).splitlines()
            )

    return "\n".join(lines)
