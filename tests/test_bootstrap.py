from __future__ import annotations

import sys
import unittest

from tests.test_support import ROOT, ensure_bootstrap_deps


class BootstrapTests(unittest.TestCase):
    def test_setup_deps_installs_expected_tools(self) -> None:
        ensure_bootstrap_deps()
        zig = ROOT / ".deps" / "ziglang" / "zig.exe"
        self.assertTrue(zig.exists(), f"missing zig executable at {zig}")

        deps_path = str(ROOT / ".deps")
        if deps_path not in sys.path:
            sys.path.insert(0, deps_path)
        import tiktoken  # pylint: disable=import-outside-toplevel

        self.assertEqual(tiktoken.__version__, "0.12.0")


if __name__ == "__main__":
    unittest.main()

