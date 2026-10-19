"""Tests for attaching chip identity review evidence to hardware inventory."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / ".github" / "skills" / "autosar-hw-code-traceability" / "scripts" / "merge_chip_identity.py"
SPEC = importlib.util.spec_from_file_location("merge_chip_identity", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class MergeChipIdentityTests(unittest.TestCase):
    def test_attaches_by_reference_without_overwriting_inventory_fields(self):
        inventory = {"components": [{"ref": "U1", "part_number": "BOM-PN", "package": "LQFP"}, {"ref": "U2", "part_number": "OTHER"}], "pins": []}
        review = {"report_type": "chip_identity_review", "decision": "unconfirmed", "component_checks": [{"reference": "U1", "checks": {"part_number": {"status": "candidate_mismatch_review_required"}}, "component_status": "unconfirmed_review_required"}], "review_gaps": [{"field": "package"}], "source_analysis_sha256": "abc"}
        merged = MODULE.merge(inventory, review)
        u1, u2 = merged["components"]
        self.assertEqual(u1["part_number"], "BOM-PN")
        self.assertEqual(u1["package"], "LQFP")
        self.assertEqual(u1["chip_identity_review"]["checks"][0]["part_number"]["status"], "candidate_mismatch_review_required")
        self.assertTrue(u1["chip_identity_review"]["human_confirmation_required"])
        self.assertNotIn("chip_identity_review", u2)
        self.assertEqual(merged["identity_review_metadata"]["components_matched"], 1)

    def test_cli_writes_merged_inventory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inventory = root / "inventory.json"
            review = root / "review.json"
            output = root / "merged.json"
            inventory.write_text(json.dumps({"components": [{"ref": "U1"}], "pins": [], "nets": []}), encoding="utf-8")
            review.write_text(json.dumps({"component_checks": [{"reference": "U1", "checks": {}}], "decision": "unconfirmed"}), encoding="utf-8")
            result = subprocess.run([sys.executable, str(SCRIPT), str(inventory), str(review), "--out", str(output)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            data = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(data["components"][0]["chip_identity_review"]["human_confirmation_required"])
            self.assertEqual(data["identity_review_metadata"]["decision"], "unconfirmed")


if __name__ == "__main__":
    unittest.main()
