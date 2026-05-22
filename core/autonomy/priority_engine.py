class PriorityEngine:

    def calculate(
        self,
        issue_type: str,
    ) -> int:

        mapping = {
            "crash": 100,
            "provider": 90,
            "runtime": 95,
            "repo": 60,
            "ui": 40,
        }

        return mapping.get(
            issue_type,
            10,
        )
