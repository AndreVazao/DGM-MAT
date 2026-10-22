from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.audit_development_callers import build_report, inspect_file, scan_python_files


class DevelopmentCallerAuditTests(unittest.TestCase):
    def test_finds_method_calls_without_importing_or_executing_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "sample.py"
            source.write_text(
                "from core.development.implementation_engine import ImplementationEngine\n"
                "engine = ImplementationEngine()\n"
                "engine.execute_implementation('plan-1')\n",
                encoding="utf-8",
            )
            findings = inspect_file(source, root)
            kinds = [item["kind"] for item in findings]
            self.assertIn("from_import", kinds)
            self.assertIn("class_call", kinds)
            self.assertTrue(any(
                item["kind"] == "method_call"
                and item["symbol"] == "execute_implementation"
                for item in findings
            ))

    def test_reports_syntax_errors_instead_of_silently_dropping_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "broken.py"
            source.write_text("def broken(:\n", encoding="utf-8")
            findings = inspect_file(source, root)
            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0]["kind"], "parse_error")

    def test_excludes_virtual_environment_and_generated_directories(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "core").mkdir()
            (root / "core" / "safe.py").write_text("x = 1\n", encoding="utf-8")
            (root / ".venv" / "lib").mkdir(parents=True)
            (root / ".venv" / "lib" / "ignored.py").write_text("x = 2\n", encoding="utf-8")
            files = scan_python_files(root)
            self.assertEqual([item.relative_to(root).as_posix() for item in files], ["core/safe.py"])

    def test_report_is_read_only_and_explicitly_limits_its_claims(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "entry.py").write_text("pass\n", encoding="utf-8")
            before = (root / "entry.py").read_bytes()
            report = build_report(root)
            self.assertEqual(report["python_files_scanned"], 1)
            self.assertTrue(any("do not prove runtime reachability" in item for item in report["limitations"]))
            self.assertEqual((root / "entry.py").read_bytes(), before)
            self.assertEqual(sorted(item.name for item in root.iterdir()), ["entry.py"])


if __name__ == "__main__":
    unittest.main()
