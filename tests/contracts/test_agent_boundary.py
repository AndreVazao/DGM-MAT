from dgm_contracts import Event

from core.agents.autonomy_agent import AutonomyAgent
from core.agents.provider_agent import ProviderAgent
from core.agents.repo_agent import RepoAgent
from core.agents.service_adapters import CoreLoggerAdapter


class RecordingProvider:
    def __init__(self):
        self.called = 0

    def run(self):
        self.called += 1


class RecordingTask:
    def __init__(self):
        self.calls = []

    def analyze_issue(self, issue_type, description, origin="repo_analysis"):
        self.calls.append((issue_type, description, origin))


def event():
    return Event(event_id="agent-test", event_type="test", source="test", target="agent", payload={})


def test_agents_use_public_event_and_injected_services():
    provider = RecordingProvider()
    task = RecordingTask()

    ProviderAgent("provider", logger=CoreLoggerAdapter(), provider_service=provider).handle_event(event())
    AutonomyAgent("autonomy", logger=CoreLoggerAdapter(), task_service=task).handle_event(event())

    assert provider.called == 1
    assert task.calls == [("repo", "Potential duplicated systems", "repo_analysis")]


def test_simple_agents_have_no_core_service_dependency_at_runtime():
    agent = RepoAgent("repo")
    agent.handle_event(event())
    assert agent.health == "healthy"
