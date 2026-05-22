from dataclasses import dataclass
from pathlib import Path


@dataclass
class RepositoryInfo:

    name: str

    path: Path

    tech_stack: list[str]

    total_files: int

    has_git: bool

    category: str
