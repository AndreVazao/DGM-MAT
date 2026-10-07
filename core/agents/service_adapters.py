"""Core-owned adapters injected into the standalone Agents boundary."""
from core.autonomy.task_engine import TaskEngine
from core.observability.logger import dgm_logger
from core.providers.provider_runtime import ProviderRuntime


class CoreLoggerAdapter:
    def info(self, message: str) -> None:
        dgm_logger.info(message)

    def error(self, message: str) -> None:
        dgm_logger.error(message)

    def critical(self, message: str) -> None:
        dgm_logger.critical(message)


class CoreProviderServiceAdapter:
    def run(self) -> None:
        ProviderRuntime().run()


class CoreTaskServiceAdapter:
    def analyze_issue(self, issue_type: str, description: str, origin: str = "repo_analysis") -> None:
        TaskEngine().analyze_issue(issue_type, description, origin=origin)
