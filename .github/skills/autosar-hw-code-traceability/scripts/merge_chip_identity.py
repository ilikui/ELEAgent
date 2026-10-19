#!/usr/bin/env python3
"""Attach chip identity review results to a hardware inventory without overwriting source fields."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def merge(inventory: dict[str, Any], review: dict[str, Any]) -> dict[str, Any]:
    components = inventory.get("components")
    if not isinstance(components, list):
        raise ValueError("Inventory must contain a components array.")
    checks = review.get("component_checks", [])
    if not isinstance(checks, list):
        raise ValueError("Identity review component_checks must be an array.")
    by_ref = {}
    for check in checks:
        if not isinstance(check, dict):
            continue
        ref = check.get("reference")
        if ref not in (None, ""):
            by_ref.setdefault(str(ref), []).append(check)
    result = json.loads(json.dumps(inventory, ensure_ascii=False))
    attached = 0
    for component in result["components"]:
        if not isinstance(component, dict) or component.get("ref") is None:
            continue
        matches = by_ref.get(str(component["ref"]), [])
        if not matches:
            continue
        # Preserve every source component field; identity review is a separate nested record.
        component["chip_identity_review"] = {
            "decision": review.get("decision", "unconfirmed"),
            "document": review.get("document", {}),
            "checks": [m.get("checks", {}) for m in matches],
            "component_status": [m.get("component_status", "unconfirmed_review_required") for m in matches],
            "review_gaps": review.get("review_gaps", []),
            "source_analysis_sha256": review.get("source_analysis_sha256"),
            "manifest_sha256": review.get("manifest_sha256"),
            "human_confirmation_required": True,
        }
        attached += 1
    result["identity_review_metadata"] = {
        "report_type": review.get("report_type", "chip_identity_review"),
        "decision": review.get("decision", "unconfirmed"),
        "source_analysis_sha256": review.get("source_analysis_sha256"),
        "human_confirmation_required": True,
        "components_matched": attached,
        "components_unmatched": max(len(result["components"]) - attached, 0),
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inventory_json", type=Path)
    parser.add_argument("identity_review_json", type=Path)
    parser.add_argument("--out", type=Path, default=Path("engineering/chip_manual/hardware_inventory_with_identity.json"))
    args = parser.parse_args()
    for path in (args.inventory_json, args.identity_review_json):
        if not path.is_file() or path.suffix.lower() != ".json":
            parser.error(f"Input must be an existing JSON file: {path}")
    try:
        inventory = json.loads(args.inventory_json.read_text(encoding="utf-8"))
        review = json.loads(args.identity_review_json.read_text(encoding="utf-8"))
        if not isinstance(inventory, dict) or not isinstance(review, dict):
            raise ValueError("Both JSON roots must be objects.")
        merged = merge(inventory, review)
        merged["identity_review_metadata"]["inventory_sha256"] = sha256(args.inventory_json)
        merged["identity_review_metadata"]["identity_report_sha256"] = sha256(args.identity_review_json)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Inventory components matched to identity review: {merged['identity_review_metadata']['components_matched']}")
    print(f"Review decision remains: {merged['identity_review_metadata']['decision']}")
    print(f"Merged inventory: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
