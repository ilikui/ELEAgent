"""Unit tests for MCP server path policy and tool wrappers."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import mcp_server


class MCPServerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        (self.root / "src").mkdir()
        (self.root / "src" / "main.c").write_text("void main(void) {}\n", encoding="utf-8")
        self.env = patch.dict(os.environ, {"ELEAGENT_WORKSPACE": str(self.root)})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def test_relative_path_resolves_inside_workspace(self):
        result = mcp_server.safe_path("src/main.c")
        self.assertEqual(result, self.root / "src" / "main.c")

    def test_absolute_path_rejected(self):
        with self.assertRaises(ValueError):
            mcp_server.safe_path(str(self.root / "src" / "main.c"))

    def test_parent_traversal_rejected(self):
        with self.assertRaises(ValueError):
            mcp_server.safe_path("../outside.txt", must_exist=False)

    def test_symlink_escape_rejected(self):
        outside = Path(self.tmp.name).parent / "outside-eleagent-test.txt"
        outside.write_text("outside", encoding="utf-8")
        link = self.root / "escape.txt"
        try:
            link.symlink_to(outside)
            with self.assertRaises(ValueError):
                mcp_server.safe_path("escape.txt")
        finally:
            outside.unlink(missing_ok=True)

    def test_tool_metadata(self):
        info = mcp_server.get_workspace_info()
        self.assertIn('"transport": "stdio"', info)
        self.assertIn("analyze_arxml", info)


if __name__ == "__main__":
    unittest.main()
