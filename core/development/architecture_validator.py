"""Fail-closed architecture validation until structural rules are implemented."""
from typing import Any

from core.development.development_models import ValidationResult


class ArchitectureValidator:
    def validate_architecture(self, changes: list[Any]) -> ValidationResult:
        """Refuse to certify changes while no architecture rules are implemented."""
        if not changes:
            return ValidationResult(
                success=False,
                errors=["No proposed changes were supplied for architecture validation."],
            )
        return ValidationResult(
            success=False,
            errors=[
                "Architecture validation rules are not implemented; changes were not certified."
            ],
        )
