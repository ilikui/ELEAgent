"""Tests for candidate table extraction from chip-manual PDFs."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import fitz

SCRIPT = Path(__file__).resolve().parents[1] / ".github" / "skills" / "autosar-hw-code-traceability" / "scripts" / "extract_chip_tables.py"


class ChipTableExtractionTests(unittest.TestCase):
    def test_writes_provenance_report_even_when_no_table_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pdf = root / "manual.pdf"
            out = root / "tables.json"
            with fitz.open() as doc:
                page = doc.new_page()
                page.insert_text((72, 72), "GPIO register description and pin function overview")
                doc.save(pdf)
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(pdf), "--out", str(out)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["document"]["pdf_page_count"], 1)
            self.assertEqual(data["tables_found"], len(data["tables"]))
            self.assertTrue(data["document"]["sha256"])
            self.assertIn("Verify every consequential value", " ".join(data["limitations"]))


if __name__ == "__main__":
    unittest.main()
