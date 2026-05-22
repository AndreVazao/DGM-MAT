from typing import Dict, List, Any, Optional
from core.event_bus.bus import Event, EventBus
from core.git_engine.git_manager import GitManager

class AutoRepair:
    def __init__(self, event_bus: EventBus, git_manager: GitManager):
        self.bus = event_bus
        self.git = git_manager

    def propose_fix(self, issue_type: str, context: Dict[str, Any]):
        """Propose a fix for a structural inconsistency."""
        proposal = {
            "issue_type": issue_type,
            "suggestion": self._get_suggestion(issue_type),
            "affected_files": context.get("files", []),
            "risk_level": "low" if issue_type == "missing_file" else "medium"
        }

        self.bus.publish(Event(
            source="repo_auto_repair",
            type="repair_proposal",
            payload=proposal,
            priority="medium"
        ))
        return proposal

    def apply_fix(self, proposal: Dict[str, Any], approved: bool = False):
        """Apply the suggested fix after approval."""
        if not approved:
            self._log_info("Fix application skipped: Approval required")
            return False

        # 1. Create safety branch
        branch_name = f"auto-repair-{proposal['issue_type']}"
        self.git.create_branch(branch_name)

        # 2. Simulate applying fix
        # In a real scenario, this would involve file system operations
        self._log_info(f"Applying fix: {proposal['suggestion']}")

        # 3. Commit and generate PR
        self.git.commit(f"Auto-repair: {proposal['issue_type']}")
        self.git.create_pull_request(
            title=f"Auto-repair fix for {proposal['issue_type']}",
            body=f"Applied suggestion: {proposal['suggestion']}",
            head=branch_name
        )

        return True

    def _get_suggestion(self, issue_type: str) -> str:
        suggestions = {
            "missing_file": "Create missing file based on template",
            "structural_inconsistency": "Normalize directory structure",
            "broken_dependency": "Update requirements or package.json",
            "architecture_drift": "Refactor to match architecture.md patterns"
        }
        return suggestions.get(issue_type, "Perform manual review")

    def _log_info(self, message: str):
        self.bus.publish(Event(
            source="repo_auto_repair",
            type="log",
            payload={"message": message},
            priority="low"
        ))
