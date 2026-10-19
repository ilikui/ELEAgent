#!/usr/bin/env python3
"""Validate traceability JSON shape and flag unresolved claims; not an AUTOSAR validator."""
import argparse
import json
import sys
from pathlib import Path

REQUIRED = ("id", "requirement", "hardware", "chip", "autosar", "software", "verification", "confidence", "status")
GROUPS = ("requirement", "hardware", "chip", "autosar", "software", "verification")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"ERROR: cannot read valid JSON: {error}", file=sys.stderr)
        return 2
    if data.get("report_type") == "schematic_to_autosar_candidate_trace":
        nodes = data.get("nodes", [])
        edges = data.get("edges", [])
        findings = data.get("findings", [])
        if not all(isinstance(value, list) for value in (nodes, edges, findings)):
            print("ERROR: graph nodes, edges and findings must be arrays", file=sys.stderr)
            return 2
        node_ids = {node.get("id") for node in nodes if isinstance(node, dict)}
        errors, warnings = [], []
        for index, edge in enumerate(edges):
            if not isinstance(edge, dict):
                errors.append(f"edge-{index}: edge must be an object")
                continue
            if edge.get("from") not in node_ids or edge.get("to") not in node_ids:
                errors.append(f"edge-{index}: references a missing node")
            if edge.get("review_state") == "candidate_unverified":
                warnings.append(f"edge-{index}: exact-name candidate remains unverified")
        for finding in findings:
            if isinstance(finding, dict):
                warnings.append(f"{finding.get('id', 'finding')}: {finding.get('gap', 'review finding')}")
        for message in errors: print("ERROR:", message)
        for message in warnings: print("WARNING:", message)
        print(f"Graph nodes: {len(nodes)}; edges: {len(edges)}; findings: {len(findings)}; errors: {len(errors)}; warnings: {len(warnings)}")
        return 1 if errors else 0
    records = data.get("records")
    if not isinstance(records, list):
        print("ERROR: top-level records must be an array", file=sys.stderr)
        return 2
    errors, warnings, seen = [], [], set()
    for index, record in enumerate(records):
        label = record.get("id", f"index-{index}")
        for field in REQUIRED:
            if field not in record:
                errors.append(f"{label}: missing field {field}")
        if label in seen:
            errors.append(f"{label}: duplicate ID")
        seen.add(label)
        for group in GROUPS:
            if not isinstance(record.get(group), dict):
                errors.append(f"{label}: {group} must be an object")
        serialized = json.dumps(record, ensure_ascii=False).casefold()
        if "unknown" in serialized or "needs_human_review" in serialized or "unverified" in serialized:
            warnings.append(f"{label}: unresolved facts remain")
        verification = record.get("verification", {})
        if verification.get("status") == "PASS" and not verification.get("evidence"):
            warnings.append(f"{label}: PASS has no verification evidence")
        software = record.get("software", {})
        if software.get("generated") is True and not software.get("generator_source"):
            warnings.append(f"{label}: generated code lacks generator_source")
    for message in errors:
        print("ERROR:", message)
    for message in warnings:
        print("WARNING:", message)
    print(f"Records: {len(records)}; errors: {len(errors)}; warnings: {len(warnings)}")
    return 1 if errors else 0

if __name__ == "__main__":
    raise SystemExit(main())
