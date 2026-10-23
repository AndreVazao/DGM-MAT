"""Fail-closed implementation validation until real validators are configured."""
from core.development.development_models import ValidationResult


class ValidationEngine:
    def validate_implementation(self, plan_id: str) -> ValidationResult:
        """Do not certify an implementation when no validation adapter ran."""
        if not isinstance(plan_id, str) or not plan_id.strip():
            return ValidationResult(
                success=False,
                errors=["A non-empty implementation plan ID is required."],
            )
        return ValidationResult(
            success=False,
            errors=[
                "Implementation validation is not configured; no checks were executed.",
                f"Plan '{plan_id.strip()}' has not been validated.",
            ],
        )
