"""Tests for PIN/signal Excel export."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from openpyxl import load_workbook

SCRIPT = Path(__file__).resolve().parents[1] / ".github" / "skills" / "autosar-hw-code-traceability" / "scripts" / "export_pin_excel.py"


class PinExcelExportTests(unittest.TestCase):
    def test_exports_mcu_and_expander_pin_rows(self):
        inventory = {
            "components": [
                {"ref": "U1", "device_type": "MCU", "part_number": "MCU-PN", "package": "LQFP", "confidence": "high"},
                {"ref": "U2", "device_type": "IO expander", "part_number": "EXP-PN", "package": "QFN", "confidence": "medium"}
            ],
            "pins": [
                {"component_ref": "U1", "pin_number": "42", "pin_name_as_drawn": "PTA3", "datasheet_function": "GPIO", "net_id": "N1", "confidence": "high"},
                {"component_ref": "U2", "pin_number": "7", "pin_name_as_drawn": "IO0", "datasheet_function": "Expander GPIO", "net_id": "N1", "confidence": "medium"}
            ],
            "nets": [{"net_id": "N1", "name_as_drawn": "SENSOR_EN", "electrical_domain": "3V3", "signal_direction": "output", "endpoints": ["U1.42", "U2.7"]}]
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "inventory.json"
            output = root / "pin_signals.xlsx"
            source.write_text(json.dumps(inventory), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(source), "--out", str(output)],
                capture_output=True, text=True, check=False
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(output.is_file())
            workbook = load_workbook(output, read_only=True, data_only=True)
            try:
                ws = workbook["PIN信号清单"]
                self.assertEqual(ws.max_row, 3)
                headers = [cell.value for cell in ws[1]]
                row_mcu = [cell.value for cell in ws[2]]
                row_expander = [cell.value for cell in ws[3]]
                self.assertEqual(row_mcu[headers.index("器件类别")], "MCU")
                self.assertEqual(row_expander[headers.index("器件类别")], "扩展芯片")
                self.assertEqual(row_mcu[headers.index("网络名（原图）")], "SENSOR_EN")
                self.assertEqual(row_expander[headers.index("引脚号")], "7")
                self.assertIn("网络与跨页", workbook.sheetnames)
                self.assertIn("器件清单", workbook.sheetnames)
            finally:
                workbook.close()

    def test_rejects_invalid_inventory_arrays(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "inventory.json"
            output = root / "pin_signals.xlsx"
            source.write_text(json.dumps({"components": {}, "pins": [], "nets": []}), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(source), "--out", str(output)],
                capture_output=True, text=True, check=False
            )
            self.assertEqual(result.returncode, 2)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
