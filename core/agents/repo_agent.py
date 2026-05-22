from shared.models.event import Event

from core.agents.base_agent import (
    BaseAgent,
)

from core.repository_intelligence.scanner import (
    RepositoryScanner,
)

from core.repository_intelligence.tree_generator import (
    build_tree,
)

from core.repository_intelligence.duplicate_detector import (
    DuplicateDetector,
)

from core.memory.memory_engine import (
    MemoryEngine,
)


class RepoAgent(BaseAgent):

    def handle_event(
        self,
        event: Event,
    ):

        self.emit_log(
            "Scanning repositories..."
        )

        scanner = RepositoryScanner()

        repos = scanner.scan()

        self.emit_log(
            f"Detected {len(repos)} repos"
        )

        detector = DuplicateDetector()

        duplicates = detector.detect(
            repos
        )

        for repo in repos:

            tree = build_tree(
                repo.path
            )

            print("\n")
            print("=" * 60)

            print(f"REPO: {repo.name}")

            print("=" * 60)

            print(tree)

        if duplicates:

            print("\n")
            print("POTENTIAL DUPLICATES")

            for item in duplicates:

                print(item)

        MemoryEngine().run()
