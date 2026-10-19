"""Tests for chip-manual PDF indexing."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import fitz

SCRIPT = Path(__file__).resolve().parents[1] / ".github" / "skills" / "autosar-hw-code-traceability" / "scripts" / "analyze_chip_manual.py"


class ChipManualAnalysisTests(unittest.TestCase):
    def test_indexes_page_topics_and_flags_low_text_pages(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pdf = root / "manual.pdf"
            out = root / "nested" / "analysis.json"
            with fitz.open() as doc:
                page = doc.new_page()
                page.insert_text((72, 72), "Pin assignment and alternate function GPIO register map errata")
                doc.new_page()
                doc.save(pdf)
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(pdf), "--out", str(out), "--min-chars", "20"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["document"]["pdf_page_count"], 2)
            self.assertEqual(data["pages"][0]["pdf_page"], 1)
            self.assertFalse(data["pages"][0]["needs_visual_review"])
            self.assertEqual(data["review_gaps"]["low_text_pages"], [2])
            topic_map = {item["topic"]: item["pdf_pages"] for item in data["topic_index"]}
            self.assertEqual(topic_map["pinout"], [1])
            self.assertEqual(topic_map["pin_mux"], [1])
            self.assertEqual(topic_map["registers"], [1])
            self.assertEqual(topic_map["errata"], [1])
            self.assertTrue(data["document"]["sha256"])


if __name__ == "__main__":
    unittest.main()
