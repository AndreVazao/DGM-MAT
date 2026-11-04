from core.observability.logger import dgm_logger
from pathlib import Path
import subprocess
from typing import Dict, Any

class SafePatchEngine:
    """
    Generates and applies reversible patches for repository modification.
    Includes security guardrails and risk assessment.
    """
    def generate_patch(self, worktree_path: Path) -> str:
        dgm_logger.info(f"SafePatchEngine: Generating patch from {worktree_path}")
        try:
            # nosem: python.lang.security.audit.dangerous-subprocess-use-audit.dangerous-subprocess-use-audit
            result = subprocess.run(  # nosec
                ["git", "-C", str(worktree_path), "diff"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError:
            return ""

    def assess_risk(self, patch: str) -> Dict[str, Any]:
        """
        Security assessment based on patch content.
        Blocks destructive commands and identifies high-risk changes.
        """
        lines = patch.splitlines()
        score = 0.0
        warnings = []
        is_blocked = False

        if len(lines) > 200:
            score += 0.3
            warnings.append("Large patch detected")

        # CRITICAL BLOCKS
        blocked_patterns = [
            "os.system", "subprocess.Popen(shell=True)", "subprocess.run(shell=True)",
            "rm -rf", "format ", "DROP TABLE", "DELETE FROM", "registry.delete",
            "shutil.rmtree", "os.remove", ".unlink()"
        ]

        # CREDENTIAL ACCESS
        credential_patterns = [".env", "secrets", "password", "api_key", "token", "access_key"]

        for line in lines:
            # Only check added lines (+)
            if line.startswith("+"):
                lower_line = line.lower()
                if any(bp.lower() in lower_line for bp in blocked_patterns):
                    score = 1.0
                    is_blocked = True
                    warnings.append(f"SECURITY BLOCK: Destructive command detected: {line.strip()}")

                if any(cp in lower_line for cp in credential_patterns):
                    score = max(score, 0.8)
                    warnings.append(f"SECURITY WARNING: Credential-like pattern detected: {line.strip()}")

        risk_level = "LOW"
        if is_blocked: risk_level = "CRITICAL"
        elif score > 0.7: risk_level = "HIGH"
        elif score > 0.4: risk_level = "MEDIUM"

        return {
            "score": min(score, 1.0),
            "level": risk_level,
            "warnings": warnings,
            "is_blocked": is_blocked
        }

    def apply_patch(self, patch: str):
        """
        Applies patch. In PHASE 41-LITE, this MUST be preceded by ApprovalManager.
        """
        risk = self.assess_risk(patch)
        if risk["is_blocked"]:
            dgm_logger.error("SafePatchEngine: REJECTED - Destructive patch detected.")
            raise SecurityError("Destructive patch execution blocked")

        dgm_logger.info("SafePatchEngine: Applying patch to main repository")
        if not patch:
            return

        try:
            # nosem: python.lang.security.audit.dangerous-subprocess-use-audit.dangerous-subprocess-use-audit
            subprocess.run(  # nosec
                ["git", "apply"],
                input=patch,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            dgm_logger.error(f"Failed to apply patch: {e}")
            raise

class SecurityError(Exception):
    pass
