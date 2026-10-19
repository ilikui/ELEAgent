"""Small standard-library smoke tests for JSON traceability and ARXML indexing."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".github" / "skills" / "autosar-hw-code-traceability" / "scripts"

class ToolingSmokeTests(unittest.TestCase):
    def test_arxml_inventory_handles_namespace(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sample.arxml").write_text(
                '<?xml version="1.0"?><AUTOSAR xmlns="http://example.test/schema">'
                '<AR-PACKAGES><AR-PACKAGE><SHORT-NAME>Pkg</SHORT-NAME></AR-PACKAGE></AR-PACKAGES>'
                '</AUTOSAR>', encoding="utf-8")
            out = root / "inventory.json"
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "inventory_arxml.py"), str(root / "sample.arxml"), "--out", str(out)],
                capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(len(data["files"]), 1)
            self.assertTrue(any(item["short_name"] == "Pkg" for item in data["files"][0]["indexed_elements"]))

    def test_traceability_checker_rejects_missing_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "bad.json"
            file.write_text('{"schema_version":"1.0","project":"test","records":[{"id":"x"}]}', encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "check_traceability.py"), str(file)],
                capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 1)
            self.assertIn("missing field hardware", result.stdout)

if __name__ == "__main__":
    unittest.main()
