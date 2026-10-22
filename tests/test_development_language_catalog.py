from __future__ import annotations

import unittest

from core.development.language_catalog import (
    get_language_profile,
    language_for_path,
    list_language_profiles,
    validation_plan_for_path,
)


class LanguageCatalogTests(unittest.TestCase):
    def test_catalogue_has_unique_ids_and_extensions(self):
        profiles = list_language_profiles()
        ids = [profile.language_id for profile in profiles]
        self.assertEqual(len(ids), len(set(ids)))
        extensions = [extension for profile in profiles for extension in profile.extensions]
        self.assertEqual(len(extensions), len(set(extensions)))
        self.assertTrue(all(profile.execution_enabled is False for profile in profiles))
        self.assertTrue(all(profile.toolchain_status == "requires_environment_probe" for profile in profiles))

    def test_resolves_priority_languages_case_insensitively(self):
        expected = {
            "src/API.PY": "python",
            "cockpit/main.ts": "typescript",
            "cockpit/view.jsx": "javascript",
            "scripts/repair.PS1": "powershell",
            "android/App.kt": "kotlin",
            "db/migration.SQL": "sql",
            "config/app.YAML": "yaml",
        }
        for path, language_id in expected.items():
            with self.subTest(path=path):
                self.assertEqual(language_for_path(path).language_id, language_id)

    def test_windows_style_paths_are_supported(self):
        self.assertEqual(language_for_path(r"C:\work\DGM-MAT\main.py").language_id, "python")

    def test_c_header_is_marked_ambiguous(self):
        profile = language_for_path("include/common.h")
        self.assertEqual(profile.language_id, "c_cpp_header_ambiguous")
        self.assertEqual(profile.category, "ambiguous")

    def test_unknown_or_extensionless_paths_fail_closed(self):
        for path in ("README", "src/unknown.xyz", "", ".", ".."):
            with self.subTest(path=path):
                self.assertIsNone(language_for_path(path))
                plan = validation_plan_for_path(path)
                self.assertEqual(plan["status"], "blocked_unknown_language")
                self.assertFalse(plan["execution_enabled"])

    def test_plan_is_metadata_only_and_never_claims_validation(self):
        plan = validation_plan_for_path("src/main.py")
        self.assertEqual(plan["status"], "plan_only")
        self.assertEqual(plan["language_id"], "python")
        self.assertFalse(plan["execution_enabled"])
        self.assertEqual(plan["toolchain_status"], "requires_environment_probe")
        self.assertIn("unit", plan["validation_stages"])

    def test_profile_lookup_rejects_unknown_and_non_string_ids(self):
        self.assertIsNone(get_language_profile("not-a-language"))
        self.assertIsNone(get_language_profile(None))


if __name__ == "__main__":
    unittest.main()
