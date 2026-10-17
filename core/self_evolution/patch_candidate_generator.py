from typing import Any


class PatchCandidateGenerator:
    """Safe placeholder until a real diff-producing implementation is connected.

    Returning a simulated diff used to let the evolution pipeline imply that a
    candidate existed when no source change had actually been generated.
    """

    def generate_patch(self, module: str) -> dict[str, Any]:
        if not isinstance(module, str) or not module.strip():
            raise ValueError("module must be a non-empty repository-relative target")
        return {
            "module": module.strip(),
            "diff": None,
            "risk_score": 100,
            "status": "NOT_IMPLEMENTED",
            "reason": "No source diff was generated; candidate generation is not wired.",
        }
