import json, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / ".github" / "skills" / "autosar-hw-code-traceability" / "scripts" / "check_traceability.py"
REPORT = ROOT / ".github" / "skills" / "autosar-hw-code-traceability" / "scripts" / "build_review_report.py"

class TraceGraphReportingTests(unittest.TestCase):
    def test_checker_and_report_surface_missing_links(self):
        graph = {
            "report_type":"schematic_to_autosar_candidate_trace",
            "summary":{"nets":1,"nodes":1,"edges":0,"findings":1},
            "nodes":[{"id":"net:N1","type":"schematic_net"}],
            "edges":[],
            "findings":[{"id":"GAP-0001","classification":"traceability_gap","severity":"warning","net_id":"N1","signal":"IGN_SENSE","gap":"no_exact_name_match_in_arxml_index","next_step":"Check the controlled ARXML."}]
        }
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/"graph.json"; output=root/"report.md"
            source.write_text(json.dumps(graph),encoding="utf-8")
            check=subprocess.run([sys.executable,str(CHECK),str(source)],capture_output=True,text=True)
            self.assertEqual(check.returncode,0,check.stdout+check.stderr)
            self.assertIn("no_exact_name_match_in_arxml_index",check.stdout)
            report=subprocess.run([sys.executable,str(REPORT),str(source),"--out",str(output)],capture_output=True,text=True)
            self.assertEqual(report.returncode,0,report.stdout+report.stderr)
            text=output.read_text(encoding="utf-8")
            self.assertIn("IGN_SENSE",text)
            self.assertIn("Check the controlled ARXML.",text)
            self.assertIn("ECUC:",text)

if __name__ == "__main__": unittest.main()
