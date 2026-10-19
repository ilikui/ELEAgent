"""Tests for candidate table extraction from chip-manual PDFs."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import fitz

SCRIPT = Path(__file__).resolve().parents[1] / ".github" / "skills" / "autosar-hw-code-traceability" / "scripts" / "extract_chip_tables.py"
SPEC = importlib.util.spec_from_file_location("extract_chip_tables", SCRIPT)
TABLE_MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(TABLE_MODULE)


class ChipTableExtractionTests(unittest.TestCase):
    def test_classifies_candidate_pin_and_register_tables(self):
        pin_topics = TABLE_MODULE.classify_table([
            ["Pin Number", "Signal Name", "Pin Description"],
            ["12", "GPIOA0", "General purpose input/output"],
        ])
        self.assertIn("pinout", pin_topics)
        register_topics = TABLE_MODULE.classify_table([
            ["Register", "Offset", "Reset Value", "Access"],
            ["CTRL", "0x10", "0x0", "RW"],
        ])
        self.assertIn("registers", register_topics)

    def test_writes_provenance_report_even_when_no_table_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pdf = root / "manual.pdf"
            out = root / "tables.json"
            with fitz.open() as doc:
                page = doc.new_page()
                page.insert_text((72, 72), "GPIO register and pin function overview")
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
