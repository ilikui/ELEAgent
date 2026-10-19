"""Tests for header-based chip manual record normalization."""
import importlib.util
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
