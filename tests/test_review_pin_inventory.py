import importlib.util, json, tempfile, unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / ".github" / "skills" / "autosar-hw-code-traceability" / "scripts" / "review_pin_inventory.py"
SPEC = importlib.util.spec_from_file_location("review_pin_inventory", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)

class ReviewPinInventoryTests(unittest.TestCase):
    def test_attaches_review_without_overwriting_source(self):
        inventory = {"components": [], "pins": [{"component_ref":"U1","pin_number":"4","net_id":"N1","review_state":"needs_review","evidence":["schematic p.2"]}], "nets":[]}
        ledger = {"reviews":[{"component_ref":"U1","pin_number":"4","state":"verified","reviewer":"reviewer-a","reviewed_at":"2026-10-19","note":"Cross-checked against controlled schematic","evidence":[{"document":"schematic.pdf","page":2}]}]}
        result = MODULE.apply_reviews(inventory, ledger)
        pin = result["pins"][0]
        self.assertEqual(pin["review_state"], "needs_review")
        self.assertEqual(pin["human_review"]["state"], "verified")
        self.assertTrue(pin["human_review"]["human_confirmation_required"])
        self.assertEqual(result["pin_review_metadata"]["pins_matched"], 1)

    def test_verified_requires_reviewer_date_and_evidence(self):
        inventory = {"components": [], "pins":[{"component_ref":"U1","pin_number":"1","net_id":"N1"}], "nets":[]}
        with self.assertRaisesRegex(ValueError, "verified review requires"):
            MODULE.apply_reviews(inventory, {"reviews":[{"component_ref":"U1","pin_number":"1","state":"verified"}]})

    def test_multiple_reviews_are_flagged_as_conflict(self):
        inventory = {"components": [], "pins":[{"component_ref":"U1","pin_number":"1","net_id":"N1"}], "nets":[]}
        ledger = {"reviews":[{"component_ref":"U1","pin_number":"1","state":"candidate"},{"component_ref":"U1","pin_number":"1","state":"conflict","note":"Contradictory source"}]}
        result = MODULE.apply_reviews(inventory, ledger)
        self.assertEqual(result["pins"][0]["human_review"]["state"], "conflict")
        self.assertEqual(result["pins"][0]["human_review"]["entry_count"], 2)

if __name__ == "__main__": unittest.main()
