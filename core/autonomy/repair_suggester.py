class RepairSuggester:

    def suggest(
        self,
        issue: str,
    ) -> list[str]:

        suggestions = []

        if "connection" in issue:

            suggestions.append(
                "Verify websocket runtime"
            )

            suggestions.append(
                "Restart API layer"
            )

        if "provider" in issue:

            suggestions.append(
                "Refresh session state"
            )

        return suggestions
