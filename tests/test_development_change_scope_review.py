from __future__ import annotations

import unittest

from core.development.change_scope_review import ChangeScope, review_change_scope


class ChangeScopeReviewTests(unittest.TestCase):
    def test_minimal_scoped_and_tested_change_passes(self):
        result = review_change_scope(ChangeScope(
            requested_outcome="Fix import bug",
            allowed_paths=("core/example.py", "tests"),
            changed_paths=("core/example.py", "tests/test_example.py"),
            tested_paths=("core/example.py", "tests/test_example.py"),
        ))
        self.assertFalse(result.blocked)
        self.assertFalse(result.requires_owner_review)
        self.assertEqual(result.findings[0].code, "minimal_scope")

    def test_out_of_scope_file_blocks_review(self):
        result = review_change_scope(ChangeScope(
            requested_outcome="Fix import bug",
            allowed_paths=("core/example.py",),
            changed_paths=("core/example.py", "docs/unrelated.md"),
            tested_paths=("core/example.py", "docs/unrelated.md"),
        ))
        self.assertTrue(result.blocked)
        self.assertIn("out_of_scope_change", {item.code for item in result.findings})

    def test_missing_scope_fails_closed(self):
        result = review_change_scope(ChangeScope(
            requested_outcome="Fix import bug",
            allowed_paths=(),
            changed_paths=(),
        ))
        self.assertTrue(result.blocked)
        self.assertIn("missing_scope", {item.code for item in result.findings})

    def test_parent_traversal_is_blocked(self):
        result = review_change_scope(ChangeScope(
            requested_outcome="Fix import bug",
            allowed_paths=("core",),
            changed_paths=("core/../secrets.txt",),
        ))
        self.assertTrue(result.blocked)
        self.assertIn("unsafe_path", {item.code for item in result.findings})

    def test_untested_changes_require_review_not_false_pass(self):
        result = review_change_scope(ChangeScope(
            requested_outcome="Fix import bug",
            allowed_paths=("core",),
            changed_paths=("core/example.py",),
        ))
        self.assertFalse(result.blocked)
        self.assertTrue(result.requires_owner_review)
        self.assertIn("untested_changes", {item.code for item in result.findings})

    def test_new_dependency_requires_explicit_justification(self):
        result = review_change_scope(ChangeScope(
            requested_outcome="Parse config",
            allowed_paths=("core",),
            changed_paths=("core/config.py",),
            tested_paths=("core/config.py",),
            new_dependencies=("yaml-lib",),
        ))
        self.assertTrue(result.blocked)
        self.assertIn("unjustified_dependency", {item.code for item in result.findings})

    def test_documented_dependency_still_requires_review(self):
        result = review_change_scope(ChangeScope(
            requested_outcome="Parse config",
            allowed_paths=("core",),
            changed_paths=("core/config.py",),
            tested_paths=("core/config.py",),
            new_dependencies=("yaml-lib",),
            justifications=(("dependency:yaml-lib", "Existing parser cannot handle required format."),),
        ))
        self.assertFalse(result.blocked)
        self.assertTrue(result.requires_owner_review)
        self.assertIn("new_dependency_review", {item.code for item in result.findings})

    def test_duplicate_capability_requires_reuse_or_justification(self):
        result = review_change_scope(ChangeScope(
            requested_outcome="Add file inventory",
            allowed_paths=("core",),
            changed_paths=("core/inventory.py",),
            tested_paths=("core/inventory.py",),
            duplicate_capabilities=("existing_file_scanner",),
        ))
        self.assertTrue(result.blocked)
        self.assertIn("duplicate_capability", {item.code for item in result.findings})

    def test_missing_requested_outcome_blocks(self):
        result = review_change_scope(ChangeScope(
            requested_outcome=" ",
            allowed_paths=("core",),
            changed_paths=(),
        ))
        self.assertTrue(result.blocked)
        self.assertIn("missing_outcome", {item.code for item in result.findings})


if __name__ == "__main__":
    unittest.main()
