from __future__ import annotations

import subprocess
import unittest
from unittest.mock import Mock, patch

from core.development.toolchain_probe import probe_toolchain, supported_tool_ids


class ToolchainProbeTests(unittest.TestCase):
    @patch("core.development.toolchain_probe.shutil.which", return_value=None)
    def test_missing_tool_is_unavailable_without_running_process(self, which):
        with patch("core.development.toolchain_probe.subprocess.run") as run:
            result = probe_toolchain("node")
        self.assertEqual(result.status, "unavailable")
        run.assert_not_called()

    def test_unknown_tool_id_is_rejected(self):
        with patch("core.development.toolchain_probe.shutil.which") as which, patch(
            "core.development.toolchain_probe.subprocess.run"
        ) as run:
            result = probe_toolchain("python; delete everything")
        self.assertEqual(result.status, "unsupported_probe")
        which.assert_not_called()
        run.assert_not_called()

    @patch("core.development.toolchain_probe.shutil.which", return_value="/usr/bin/python")
    @patch("core.development.toolchain_probe.subprocess.run")
    def test_available_tool_uses_fixed_args_and_no_shell(self, run, which):
        run.return_value = Mock(returncode=0, stdout="Python 3.12.1\n", stderr="")
        result = probe_toolchain("python", timeout_seconds=50)
        self.assertEqual(result.status, "available")
        self.assertEqual(result.version, "Python 3.12.1")
        args, kwargs = run.call_args
        self.assertEqual(args[0], ["/usr/bin/python", "--version"])
        self.assertIs(kwargs["shell"], False)
        self.assertEqual(kwargs["timeout"], 5.0)

    @patch("core.development.toolchain_probe.shutil.which", return_value="/usr/bin/node")
    @patch("core.development.toolchain_probe.subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="node", timeout=2))
    def test_timeout_is_reported_not_hidden(self, run, which):
        result = probe_toolchain("node", timeout_seconds=2)
        self.assertEqual(result.status, "timeout")
        self.assertEqual(result.executable_path, "/usr/bin/node")

    @patch("core.development.toolchain_probe.shutil.which", return_value="/usr/bin/go")
    @patch("core.development.toolchain_probe.subprocess.run")
    def test_nonzero_exit_is_failed(self, run, which):
        run.return_value = Mock(returncode=1, stdout="", stderr="go error")
        result = probe_toolchain("go")
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.version, "go error")

    def test_allowlist_is_fixed_and_sorted(self):
        tool_ids = supported_tool_ids()
        self.assertEqual(tool_ids, tuple(sorted(set(tool_ids))))
        self.assertIn("python", tool_ids)
        self.assertIn("pwsh", tool_ids)


if __name__ == "__main__":
    unittest.main()
