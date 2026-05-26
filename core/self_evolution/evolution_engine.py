from typing import List, Dict, Any
from core.observability.logger import dgm_logger
from core.self_evolution.patch_candidate_generator import PatchCandidateGenerator
from core.self_evolution.safety_validator import SafetyValidator
from core.self_evolution.sandbox_runner import SandboxRunner

class EvolutionEngine:
    def __init__(self):
        self.patch_gen = PatchCandidateGenerator()
        self.validator = SafetyValidator()
        self.sandbox = SandboxRunner()

    async def propose_evolution(self, target_module: str):
        dgm_logger.info(f"EvolutionEngine: Proposing evolution for {target_module}")
        patch = self.patch_gen.generate_patch(target_module)

        if self.validator.validate(patch):
            dgm_logger.info("EvolutionEngine: Patch validated. Running in sandbox.")
            success = await self.sandbox.run(patch)
            if success:
                dgm_logger.info("EvolutionEngine: Sandbox run successful. Patch ready for promotion.")
                return patch
        else:
            dgm_logger.warning("EvolutionEngine: Patch failed safety validation.")
        return None
