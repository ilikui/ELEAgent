import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".github" / "skills" / "autosar-hw-code-traceability" / "scripts" / "analyze_arxml.py"

class ArxmlAnalysisTests(unittest.TestCase):
    def test_reference_to_unique_short_name_path_is_resolved(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            (base / "target.arxml").write_text(
                '<AUTOSAR xmlns="urn:autosar"><AR-PACKAGES><AR-PACKAGE>'
                '<SHORT-NAME>Demo</SHORT-NAME><ELEMENTS><APPLICATION-SW-COMPONENT-TYPE>'
                '<SHORT-NAME>SensorSwc</SHORT-NAME></APPLICATION-SW-COMPONENT-TYPE>'
                '</ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>', encoding="utf-8")
            (base / "source.arxml").write_text(
                '<AUTOSAR xmlns="urn:autosar"><AR-PACKAGES><AR-PACKAGE>'
                '<SHORT-NAME>Demo</SHORT-NAME><ELEMENTS><SOME-CONTAINER>'
                '<SHORT-NAME>Config</SHORT-NAME><TYPE-TREF DEST="APPLICATION-SW-COMPONENT-TYPE">'
                '/Demo/SensorSwc</TYPE-TREF></SOME-CONTAINER></ELEMENTS>'
                '</AR-PACKAGE></AR-PACKAGES></AUTOSAR>', encoding="utf-8")
            output = base / "analysis.json"
            result = subprocess.run([sys.executable, str(SCRIPT), str(base), "--out", str(output)],
                                    text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            data = json.loads(output.read_text(encoding="utf-8"))
            refs = [r for r in data["references"] if r["reference"] == "/Demo/SensorSwc"]
            self.assertEqual(len(refs), 1)
            self.assertEqual(refs[0]["resolution"], "resolved_unique")
            self.assertTrue(refs[0]["xpath"].startswith("/AUTOSAR[1]/"))
            self.assertTrue(refs[0]["target_candidates"][0]["xpath"])

    def test_duplicate_target_paths_are_marked_ambiguous(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            for filename in ("one.arxml", "two.arxml"):
                (base / filename).write_text(
                    '<AUTOSAR><AR-PACKAGES><AR-PACKAGE><SHORT-NAME>Pkg</SHORT-NAME>'
                    '<ELEMENTS><SOME-TYPE><SHORT-NAME>Item</SHORT-NAME></SOME-TYPE></ELEMENTS>'
                    '</AR-PACKAGE></AR-PACKAGES></AUTOSAR>', encoding="utf-8")
            (base / "source.arxml").write_text(
                '<AUTOSAR><SOME-REF>/Pkg/Item</SOME-REF></AUTOSAR>', encoding="utf-8")
            output = base / "analysis.json"
            result = subprocess.run([sys.executable, str(SCRIPT), str(base), "--out", str(output)],
                                    text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            data = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(any(r["resolution"] == "ambiguous_multiple_targets" for r in data["references"]))

if __name__ == "__main__":
    unittest.main()
