# Path: C:\\ProgramasGodMode\\DGM-MAT\\tests\\organization\\test_help_seeking.py
"""Regression tests for help-seeking and zero-cost-by-default policy."""
import unittest

from core.organization.help_seeking import HelpAction, HelpContext, HelpSeekingPolicy


class HelpSeekingPolicyTests(unittest.TestCase):
    def test_missing_goal_asks_user(self):
        decision = HelpSeekingPolicy.decide(HelpContext(goal=" "))
        self.assertEqual(decision.action, HelpAction.ASK_USER)
        self.assertFalse(decision.spending_allowed)

    def test_free_option_precedes_paid_option(self):
        decision = HelpSeekingPolicy.decide(HelpContext(
            goal="Diagnose failing test",
            unknowns=("Which dependency fails?",),
            free_options=("Run local focused test", "Read project docs"),
            paid_option_only=True,
            paid_option_description="Paid model call",
        ))
        self.assertEqual(decision.action, HelpAction.INVESTIGATE_FREE)
        self.assertFalse(decision.spending_allowed)
        self.assertIn("Run local focused test", decision.metadata["free_options"])

    def test_available_specialist_is_preferred_to_external_spend(self):
        decision = HelpSeekingPolicy.decide(HelpContext(
            goal="Review API authentication",
            unknowns=("Route scope coverage",),
            specialist_available=True,
            paid_option_only=True,
        ))
        self.assertEqual(decision.action, HelpAction.DELEGATE_SPECIALIST)
        self.assertFalse(decision.spending_allowed)
        self.assertIn("Goal:", decision.help_request)

    def test_paid_only_path_blocks_without_spending(self):
        decision = HelpSeekingPolicy.decide(HelpContext(
            goal="Complete task",
            paid_option_only=True,
            paid_option_description="External API call, price not verified",
        ))
        self.assertEqual(decision.action, HelpAction.BLOCKED)
        self.assertFalse(decision.spending_allowed)
        self.assertIn("not authorized", decision.help_request.lower())

    def test_retry_limit_blocks_and_preserves_help_context(self):
        decision = HelpSeekingPolicy.decide(HelpContext(
            goal="Repair build",
            attempted_steps=("Run focused test", "Run full suite"),
            evidence=("Same import error on both runs",),
            max_attempts_reached=True,
        ))
        self.assertEqual(decision.action, HelpAction.BLOCKED)
        self.assertIn("Same import error", decision.help_request)
        self.assertIn("attempt budget", decision.reason)

    def test_user_decision_takes_priority(self):
        decision = HelpSeekingPolicy.decide(HelpContext(
            goal="Choose deployment target",
            user_decision_required=True,
            free_options=("Local dry run",),
        ))
        self.assertEqual(decision.action, HelpAction.ASK_USER)

    def test_spending_gate_requires_all_conditions(self):
        self.assertTrue(HelpSeekingPolicy.may_spend(
            explicit_approval=True, cost_known=True, within_approved_limit=True
        ))
        self.assertFalse(HelpSeekingPolicy.may_spend(
            explicit_approval=False, cost_known=True, within_approved_limit=True
        ))
        self.assertFalse(HelpSeekingPolicy.may_spend(
            explicit_approval=True, cost_known=False, within_approved_limit=True
        ))
        self.assertFalse(HelpSeekingPolicy.may_spend(
            explicit_approval=True, cost_known=True, within_approved_limit=False
        ))
        self.assertFalse(HelpSeekingPolicy.may_spend(
            explicit_approval=1, cost_known=True, within_approved_limit=True
        ))

    def test_help_request_contains_attempts_evidence_and_specific_ask(self):
        request = HelpSeekingPolicy.build_request(HelpContext(
            goal="Find failing route",
            known_facts=("Backend is loopback-only",),
            unknowns=("Which client uses the route?",),
            attempted_steps=("Search API router",),
            evidence=("Route returns 401 without token",),
        ), "Identify client migration needed.")
        self.assertIn("Backend is loopback-only", request)
        self.assertIn("Search API router", request)
        self.assertIn("Route returns 401", request)
        self.assertIn("Identify client migration needed", request)


if __name__ == "__main__":
    unittest.main()
