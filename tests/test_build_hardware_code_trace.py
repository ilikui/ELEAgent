import importlib.util, unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / ".github" / "skills" / "autosar-hw-code-traceability" / "scripts" / "build_hardware_code_trace.py"
SPEC = importlib.util.spec_from_file_location("build_hardware_code_trace", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)

class HardwareCodeTraceTests(unittest.TestCase):
    def test_exact_name_candidates_and_missing_link_gaps(self):
        inventory = {
            "components":[{"ref":"U1","part_number":"MCU-X","device_type":"MCU"}],
            "pins":[{"component_ref":"U1","pin_number":"12","pin_name_as_drawn":"PTA0","net_id":"N1","signal_name":"IGN_SENSE","evidence":[{"page":3}]}],
            "nets":[{"net_id":"N1","name_as_drawn":"IGN_SENSE","review_state":"needs_review"}]
        }
        arxml = {"elements":[{"file":"Ecuc.arxml","tag":"ECUC-CONTAINER-VALUE","short_name":"IGN_SENSE","canonical_path":"/Config/IGN_SENSE","xpath":"/AUTOSAR[1]/X[1]"}],"references":[]}
        source = {"hits":[{"path":"src/IoHwAb.c","line":42,"term":"IGN_SENSE","symbol":"IoHwAb_ReadIgnition"}]}
        graph = MODULE.build_graph(inventory, arxml, source)
        self.assertTrue(any(e["relation"] == "schematic_net_has_pin" for e in graph["edges"]))
        self.assertTrue(any(e["relation"] == "exact_name_candidate" for e in graph["edges"]))
        self.assertTrue(any(n.get("candidate_layer_tags") == ["ECUC"] for n in graph["nodes"] if n["type"] == "arxml_candidate"))
        self.assertTrue(graph["human_confirmation_required"])

    def test_identity_conflict_and_missing_pin_evidence_are_flagged(self):
        inventory = {
            "components": [{
                "ref":"U9", "part_number":"BOM-PN", "package":"LQFP",
                "chip_identity_review":{"checks":[{"part_number":{"status":"candidate_mismatch_review_required"}}]}
            }],
            "pins":[{"component_ref":"U9","pin_number":"3","net_id":"N9","signal_name":"RESET_N"}],
            "nets":[{"net_id":"N9","name_as_drawn":"RESET_N","review_state":"conflict"}]
        }
        graph = MODULE.build_graph(inventory)
        gaps = {finding["gap"] for finding in graph["findings"]}
        self.assertIn("chip_identity_mismatch_or_conflict", gaps)
        self.assertIn("pin_mapping_missing_evidence", gaps)
        self.assertIn("net_connectivity_conflict", gaps)
        self.assertTrue(any(edge["relation"] == "component_has_pin" for edge in graph["edges"]))

    def test_missing_arxml_and_source_are_explicit_gaps(self):
        graph = MODULE.build_graph({"components":[],"pins":[],"nets":[{"net_id":"N2","name_as_drawn":"UNKNOWN_NET"}]})
        gaps = {item["gap"] for item in graph["findings"]}
        self.assertIn("net_has_no_linked_pin_records", gaps)
        self.assertIn("no_exact_name_match_in_arxml_index", gaps)
        self.assertIn("no_exact_name_match_in_source_search_results", gaps)

if __name__ == "__main__": unittest.main()
