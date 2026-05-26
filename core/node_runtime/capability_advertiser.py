from typing import List

class CapabilityAdvertiser:
    def get_my_capabilities(self) -> List[str]:
        return [
            "local_inference",
            "repo_analysis",
            "autonomous_patching"
        ]
