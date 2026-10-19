#!/usr/bin/env python3
"""Apply a separate, auditable human-review ledger to hardware inventory pins.

Review states describe evidence review only; they are not functional-safety approval.
Original inventory fields and source evidence are never overwritten.
"""
from __future__ import annotations
import argparse, hashlib, json
from datetime import datetime
from pathlib import Path
from typing import Any

STATES = {"candidate", "verified", "conflict", "rejected"}

def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def key(item: dict[str, Any]) -> tuple[str, str, str]:
    return (str(item.get("component_ref", item.get("ref", ""))), str(item.get("pin_number", "")))

def apply_reviews(inventory: dict[str, Any], ledger: dict[str, Any]) -> dict[str, Any]:
    pins = inventory.get("pins")
    reviews = ledger.get("reviews")
    if not isinstance(pins, list) or not isinstance(reviews, list):
        raise ValueError("Inventory pins and ledger reviews must be arrays.")
    indexed: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for review in reviews:
        if not isinstance(review, dict):
            raise ValueError("Every review entry must be an object.")
        state = review.get("state", "candidate")
        if state not in STATES:
            raise ValueError(f"Unsupported review state {state!r}; expected one of {sorted(STATES)}.")
        if not review.get("component_ref") or review.get("pin_number") in (None, ""):
            raise ValueError("Each review requires component_ref and pin_number.")
        if state == "verified":
            if not review.get("reviewer") or not review.get("reviewed_at") or not review.get("evidence"):
                raise ValueError("verified review requires reviewer, reviewed_at and evidence.")
        if state in {"conflict", "rejected"} and not review.get("note"):
            raise ValueError(f"{state} review requires a note explaining the decision.")
        indexed.setdefault(key(review), []).append(review)
    result = json.loads(json.dumps(inventory, ensure_ascii=False))
    matched = 0
    for pin in result["pins"]:
        if not isinstance(pin, dict):
            continue
        matches = indexed.get(key(pin), [])
        if not matches:
            continue
        # Multiple ledger entries remain visible; latest order is not treated as truth.
        pin["human_review"] = {
            "entries": matches,
            "state": matches[-1].get("state", "candidate") if len(matches) == 1 else "conflict",
            "entry_count": len(matches),
            "human_confirmation_required": True,
            "meaning": "Evidence review state only; not engineering or functional-safety approval."
        }
        matched += 1
    result["pin_review_metadata"] = {
        "ledger_schema_version": ledger.get("schema_version", "1.0"),
        "inventory_sha256": inventory.get("source_sha256"),
        "reviews_supplied": len(reviews),
        "pins_matched": matched,
        "reviews_unmatched": sum(1 for review in reviews if key(review) not in {key(p) for p in result["pins"] if isinstance(p, dict)}),
        "applied_at_utc": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "ledger_sha256": ledger.get("ledger_sha256"),
        "human_confirmation_required": True
    }
    return result

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inventory_json", type=Path)
    parser.add_argument("review_ledger_json", type=Path)
    parser.add_argument("--out", type=Path, default=Path("engineering/hardware/hardware_inventory_reviewed.json"))
    args = parser.parse_args()
    try:
        for path in (args.inventory_json, args.review_ledger_json):
            if not path.is_file() or path.suffix.lower() != ".json":
                raise ValueError(f"Input must be an existing JSON file: {path}")
        inventory = json.loads(args.inventory_json.read_text(encoding="utf-8"))
        ledger = json.loads(args.review_ledger_json.read_text(encoding="utf-8"))
        if not isinstance(inventory, dict) or not isinstance(ledger, dict):
            raise ValueError("Both JSON roots must be objects.")
        ledger["ledger_sha256"] = sha256(args.review_ledger_json)
        result = apply_reviews(inventory, ledger)
        result["pin_review_metadata"]["inventory_file_sha256"] = sha256(args.inventory_json)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"PINs with review entries: {result['pin_review_metadata']['pins_matched']}")
        print(f"Unmatched review entries: {result['pin_review_metadata']['reviews_unmatched']}")
        print(f"Output: {args.out}")
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"PIN review failed: {exc}")
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
