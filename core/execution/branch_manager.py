class BranchManager:
    @staticmethod
    def generate_branch_name(agent_name: str, task_id: str) -> str:
        return f"agent/{agent_name}/{task_id}"
