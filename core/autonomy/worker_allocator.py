class WorkerAllocator:

    def allocate(
        self,
        issue_type: str,
    ) -> str:

        mapping = {
            "runtime": "runtime-agent",
            "provider": "provider-agent",
            "repo": "repo-agent",
            "ui": "ui-agent",
        }

        return mapping.get(
            issue_type,
            "general-agent",
        )
