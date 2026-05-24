from typing import List, Dict, Any, Optional
from core.ecosystem.ecosystem_models import EcosystemRole
from core.repository_intelligence.repo_importer import RepoImporter
from core.observability.logger import dgm_logger

class GoalEngine:
    """
    DGM-MAT Goal Engine (v6).
    Translates intent into a sequence of actionable repository imports and module creations.
    """
    def __init__(self, importer: Optional[RepoImporter] = None):
        self.importer = importer or RepoImporter()

    def parse_goal(self, intent: str) -> List[str]:
        """
        Parses intent into required capability roles.
        """
        intent = intent.lower()
        required_roles = []

        if any(k in intent for k in ["trad", "finance", "market"]):
            required_roles.append("finance")
        if any(k in intent for k in ["ai", "agent", "llm"]):
            required_roles.append("labs")
            required_roles.append("providers")
        if any(k in intent for k in ["automation", "workflow"]):
            required_roles.append("connectors")
        if any(k in intent for k in ["os", "system", "platform"]):
            required_roles.append("core")
            required_roles.append("infra")

        return required_roles

    def create_plan(self, intent: str) -> List[Dict[str, Any]]:
        """
        Generates an action plan (imports) to satisfy the goal.
        """
        required_roles = self.parse_goal(intent)
        plan = []

        # Knowledge-based mapping of roles to recommended repos
        role_to_repo = {
            "finance": "https://github.com/freqtrade/freqtrade",
            "labs": "https://github.com/xtekky/gpt4free",
            "providers": "https://github.com/tashfeenahmed/freellmapi",
            "connectors": "https://github.com/n8n-io/n8n", # Note: using mock/real URLs
            "core": "https://github.com/temporalio/temporal",
            "infra": "https://github.com/qdrant/qdrant"
        }

        for role in required_roles:
            if role in role_to_repo:
                plan.append({
                    "action": "import",
                    "url": role_to_repo[role],
                    "role": role,
                    "reason": f"Required for {intent} ({role} role)"
                })

        return plan

    def execute_plan(self, plan: List[Dict[str, Any]], mode: str = "SAFE") -> List[Dict[str, Any]]:
        """
        Executes the generated plan.
        """
        results = []
        for step in plan:
            if step["action"] == "import":
                dgm_logger.info(f"Goal Engine: Planned import of {step['url']} for {step['role']}")

                if mode == "AUTO":
                    try:
                        res = self.importer.import_repo(step["url"], category_override=step["role"])
                        results.append({**step, "status": "success", "details": res})
                    except Exception as e:
                        dgm_logger.error(f"Goal Engine: Failed to execute import for {step['url']}: {e}")
                        results.append({**step, "status": "error", "message": str(e)})
                else:
                    results.append({**step, "status": "simulated"})

        return results
