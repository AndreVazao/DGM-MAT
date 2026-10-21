from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.governance.progressive_trust import ProgressiveTrustRegistry


class ProgressiveTrustRegistryTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.registry = ProgressiveTrustRegistry(Path(self.tempdir.name) / "trust.json")

    def tearDown(self):
        self.tempdir.cleanup()

    def delegate(self, **overrides):
        values = {
            "actor": "André",
            "category": "routine_documentation",
            "scope": "programming",
            "max_risk": "low",
            "min_verified_successes": 3,
            "rationale": "Delegação limitada a documentação reversível.",
        }
        values.update(overrides)
        return self.registry.grant_delegation(**values)

    def add_successes(self, count=3):
        for index in range(count):
            self.registry.record_feedback(
                category="routine_documentation", scope="programming",
                outcome="approved", rationale=f"Resultado revisto {index}",
                risk="low", reversible=True, verified_success=True,
            )

    def test_history_alone_never_grants_authority(self):
        self.add_successes(5)
        result = self.registry.evaluate(
            category="routine_documentation", scope="programming", risk="low"
        )
        self.assertFalse(result["autonomous_decision_allowed"])
        self.assertFalse(result["execution_permitted"])

    def test_owner_delegation_requires_verified_success_pattern(self):
        delegation = self.delegate()
        before = self.registry.evaluate(
            category="routine_documentation", scope="programming", risk="low"
        )
        self.assertFalse(before["autonomous_decision_allowed"])
        self.add_successes()
        after = self.registry.evaluate(
            category="routine_documentation", scope="programming", risk="low"
        )
        self.assertTrue(after["autonomous_decision_allowed"])
        self.assertEqual(after["matched_delegation_id"], delegation["delegation_id"])
        self.assertFalse(after["execution_permitted"])

    def test_rejection_or_correction_resets_success_run(self):
        self.delegate()
        self.add_successes(3)
        self.registry.record_feedback(
            category="routine_documentation", scope="programming",
            outcome="changed", rationale="André pediu uma alteração",
            risk="low", reversible=True,
        )
        result = self.registry.evaluate(
            category="routine_documentation", scope="programming", risk="low"
        )
        self.assertFalse(result["autonomous_decision_allowed"])
        self.assertEqual(result["verified_successes"], 0)

    def test_scope_risk_and_material_change_are_strict(self):
        self.delegate()
        self.add_successes()
        other_scope = self.registry.evaluate(
            category="routine_documentation", scope="human_resources", risk="low"
        )
        high_risk = self.registry.evaluate(
            category="routine_documentation", scope="programming", risk="high"
        )
        changed = self.registry.evaluate(
            category="routine_documentation", scope="programming", risk="low",
            materially_changed=True,
        )
        self.assertFalse(other_scope["autonomous_decision_allowed"])
        self.assertFalse(high_risk["autonomous_decision_allowed"])
        self.assertFalse(changed["autonomous_decision_allowed"])

    def test_protected_boundary_blocks_even_with_delegation_and_history(self):
        self.delegate()
        self.add_successes()
        result = self.registry.evaluate(
            category="routine_documentation", scope="programming", risk="low",
            protected_boundaries=["security_boundary"],
        )
        self.assertFalse(result["autonomous_decision_allowed"])

    def test_only_owner_can_grant_or_revoke_delegation(self):
        with self.assertRaisesRegex(ValueError, "only the system owner"):
            self.delegate(actor="CEO")
        delegation = self.delegate()
        with self.assertRaisesRegex(ValueError, "only the system owner"):
            self.registry.revoke_delegation(
                actor="CEO", delegation_id=delegation["delegation_id"], rationale="No"
            )
        revoked = self.registry.revoke_delegation(
            actor="André", delegation_id=delegation["delegation_id"], rationale="Rever âmbito"
        )
        self.assertFalse(revoked["active"])

    def test_corrupt_store_is_not_overwritten(self):
        self.registry.path.write_text("{broken", encoding="utf-8")
        with self.assertRaises(RuntimeError):
            self.registry.record_feedback(
                category="routine_documentation", scope="programming",
                outcome="approved", rationale="Test", risk="low",
                reversible=True, verified_success=True,
            )
        self.assertEqual(self.registry.path.read_text(encoding="utf-8"), "{broken")


if __name__ == "__main__":
    unittest.main()
