"""Tests for header-based chip manual record normalization."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / ".github" / "skills" / "autosar-hw-code-traceability" / "scripts" / "normalize_chip_tables.py"
SPEC = importlib.util.spec_from_file_location("normalize_chip_tables", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class NormalizeChipTablesTests(unittest.TestCase):
    def test_maps_unambiguous_pin_headers(self):
        mapped = MODULE.map_headers(["Pin Number", "Signal Name", "Pin Description"])
        self.assertEqual(mapped["pin_number"], 0)
        self.assertEqual(mapped["pin_name"], 1)
        self.assertEqual(mapped["pin_function"], 2)

    def test_ambiguous_duplicate_header_is_not_mapped(self):
        mapped = MODULE.map_headers(["Register", "Address", "Address"])
        self.assertNotIn("address", mapped)

    def test_preserves_missing_cells_as_none(self):
        self.assertIsNone(MODULE.cell(["GPIOA0"], 3))

    def test_cli_preserves_page_and_normalizes_data_row_not_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "tables.json"
            output = root / "records.json"
            source.write_text(json.dumps({
                "document": {"sha256": "abc123", "pdf_page_count": 1},
                "tables": [{
                    "table_id": "pdf-page-4-table-1",
                    "pdf_page": 4,
                    "candidate_topics": ["pinout"],
                    "header": ["Pin Number", "Signal Name", "Pin Description"],
                    "rows": [
                        ["Pin Number", "Signal Name", "Pin Description"],
                        ["12", "GPIOA0", "General purpose input/output"],
                    ],
                    "evidence": {"document_sha256": "abc123"},
                }],
            }), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(source), "--out", str(output)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["records_created"], 1)
            record = report["records"][0]
            self.assertEqual(record["pdf_page"], 4)
            self.assertEqual(record["values"]["pin_number"], "12")
            self.assertEqual(record["values"]["pin_name"], "GPIOA0")
            self.assertEqual(record["review_status"], "unreviewed")
            self.assertEqual(record["raw_row"][0], "12")


if __name__ == "__main__":
    unittest.main()
