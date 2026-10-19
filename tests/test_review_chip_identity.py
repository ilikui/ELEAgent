"""Tests for conservative chip identity review."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / ".github" / "skills" / "autosar-hw-code-traceability" / "scripts" / "review_chip_identity.py"
SPEC = importlib.util.spec_from_file_location("review_chip_identity", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class ReviewChipIdentityTests(unittest.TestCase):
    def test_extracts_only_labelled_candidates_with_page_evidence(self):
        report = {"pages": [{"pdf_page": 2, "text": "Ordering Part Number: MPC5748G Package: LQFP Revision: 3.1 Silicon Revision: B"}]}
        found = MODULE.extract_candidates(report)
        self.assertEqual(found["part_number"][0]["value"], "MPC5748G")
        self.assertEqual(found["part_number"][0]["pdf_page"], 2)
        self.assertEqual(found["package"][0]["value"], "LQFP")
        self.assertEqual(found["datasheet_revision"][0]["value"], "3.1")
        self.assertEqual(found["silicon_revision"][0]["value"], "B")

    def test_match_is_never_auto_approved(self):
        result = MODULE.compare("MPC5748G", [{"value": "MPC5748G", "pdf_page": 2}])
        self.assertEqual(result["status"], "candidate_exact_match_unconfirmed")
        self.assertTrue(result["human_confirmation_required"])

    def test_cli_records_mismatch_and_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "analysis.json"
            manifest = root / "bom.json"
            output = root / "review.json"
            source.write_text(json.dumps({"document": {"sha256": "pdfhash", "pdf_page_count": 1}, "pages": [{"pdf_page": 1, "text": "Part Number: ABC123 Package: QFN"}]}), encoding="utf-8")
            manifest.write_text(json.dumps({"components": [{"reference": "U1", "part_number": "XYZ999", "package": "QFN"}]}), encoding="utf-8")
            result = subprocess.run([sys.executable, str(SCRIPT), str(source), "--manifest", str(manifest), "--out", str(output)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            data = json.loads(output.read_text(encoding="utf-8"))
            checks = data["component_checks"][0]["checks"]
            self.assertEqual(checks["part_number"]["status"], "candidate_mismatch_review_required")
            self.assertEqual(checks["package"]["status"], "candidate_exact_match_unconfirmed")
            self.assertEqual(data["decision"], "unconfirmed")
            self.assertTrue(data["source_analysis_sha256"])


if __name__ == "__main__":
    unittest.main()
