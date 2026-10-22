from __future__ import annotations

import unittest

from core.development.architecture_validator import ArchitectureValidator
from core.development.development_models import ImplementationStatus
from core.development.feature_planner import FeaturePlanner
from core.development.validation_engine import ValidationEngine


class DevelopmentSafetyGateTests(unittest.TestCase):
    def test_implementation_validation_never_claims_success_without_checks(self):
        result = ValidationEngine().validate_implementation("feat_123")
        self.assertFalse(result.success)
        self.assertTrue(any("not configured" in error for error in result.errors))

    def test_empty_plan_id_is_rejected(self):
        result = ValidationEngine().validate_implementation(" ")
        self.assertFalse(result.success)
        self.assertTrue(any("plan ID" in error for error in result.errors))

    def test_architecture_validator_fails_closed_for_empty_changes(self):
        result = ArchitectureValidator().validate_architecture([])
        self.assertFalse(result.success)
        self.assertTrue(result.errors)

    def test_architecture_validator_does_not_certify_unchecked_changes(self):
        result = ArchitectureValidator().validate_architecture([{"file_path": "core/example.py"}])
        self.assertFalse(result.success)
        self.assertTrue(any("not implemented" in error for error in result.errors))

    def test_empty_feature_request_is_rejected(self):
        with self.assertRaises(ValueError):
            FeaturePlanner().plan_feature("  ")

    def test_feature_ids_are_stable_and_plans_remain_planning_only(self):
        planner = FeaturePlanner()
        first = planner.plan_feature("Improve the API")
        second = planner.plan_feature("Improve the API")
        different = planner.plan_feature("Improve the API safely")
        self.assertEqual(first.feature_id, second.feature_id)
        self.assertNotEqual(first.feature_id, different.feature_id)
        self.assertEqual(first.status, ImplementationStatus.PLANNING)


if __name__ == "__main__":
    unittest.main()
