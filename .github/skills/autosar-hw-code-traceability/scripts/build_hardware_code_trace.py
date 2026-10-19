#!/usr/bin/env python3
"""Build a conservative schematic-net to AUTOSAR/source candidate trace graph.

Only exact, normalized string matches are proposed. Matching names are discovery
hints, not proof of electrical connectivity or runtime data flow.
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from typing import Any

def norm(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"[^a-z0-9]+", "", str(value).casefold())

def load_object(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return data

def build_graph(inventory: dict[str, Any], arxml: dict[str, Any] | None = None,
                source: dict[str, Any] | None = None) -> dict[str, Any]:
    components = inventory.get("components", [])
    pins = inventory.get("pins", [])
    nets = inventory.get("nets", [])
    if not all(isinstance(x, list) for x in (components, pins, nets)):
        raise ValueError("Inventory components, pins and nets must be arrays.")
    comp_by_ref = {str(c.get("ref")): c for c in components if isinstance(c, dict) and c.get("ref") is not None}
    pins_by_net: dict[str, list[dict[str, Any]]] = {}
    for pin in pins:
        if isinstance(pin, dict) and pin.get("net_id") not in (None, ""):
            pins_by_net.setdefault(str(pin["net_id"]), []).append(pin)
    arxml_elements = (arxml or {}).get("elements", [])
    arxml_refs = (arxml or {}).get("references", [])
    source_hits = (source or {}).get("hits", (source or {}).get("matches", []))
    if not isinstance(arxml_elements, list): arxml_elements = []
    if not isinstance(arxml_refs, list): arxml_refs = []
    if not isinstance(source_hits, list): source_hits = []
    nodes, edges, findings = [], [], []
    for net in nets:
        if not isinstance(net, dict): continue
        net_id = str(net.get("net_id", ""))
        net_name = net.get("name_as_drawn") or net.get("normalized_name")
        nid = f"net:{net_id or norm(net_name) or 'unknown'}"
        nodes.append({"id": nid, "type": "schematic_net", "net_id": net_id or None,
                      "name_as_drawn": net.get("name_as_drawn"), "normalized_name": net.get("normalized_name"),
                      "review_state": net.get("review_state", "unknown"), "evidence": net.get("evidence", [])})
        matched_pins = pins_by_net.get(net_id, [])
        if not matched_pins:
            findings.append({"id": f"GAP-{len(findings)+1:04d}", "classification": "evidence_gap",
                             "severity": "warning", "net_id": net_id, "signal": net_name,
                             "gap": "net_has_no_linked_pin_records", "next_step": "Confirm schematic endpoints and pin-to-net mapping."})
        for pin in matched_pins:
            ref = str(pin.get("component_ref", ""))
            component = comp_by_ref.get(ref, {})
            pid = f"pin:{ref}:{pin.get('pin_number', 'unknown')}:{net_id}"
            nodes.append({"id": pid, "type": "component_pin", "component_ref": ref,
                          "component_part_number": component.get("part_number"),
                          "pin_number": pin.get("pin_number"), "pin_name_as_drawn": pin.get("pin_name_as_drawn"),
                          "datasheet_function": pin.get("datasheet_function") or pin.get("function"),
                          "review_state": pin.get("human_review", {}).get("state", pin.get("review_state", "unknown")),
                          "evidence": pin.get("evidence", [])})
            edges.append({"from": nid, "to": pid, "relation": "schematic_net_has_pin",
                          "evidence": pin.get("evidence", []), "review_state": pin.get("review_state", "unknown")})
        token_set = {norm(net_name)}
        token_set.update(norm(p.get("signal_name")) for p in matched_pins if isinstance(p, dict))
        token_set.discard("")
        ar_matches = []
        for item in arxml_elements:
            if not isinstance(item, dict): continue
            searchable = [item.get("short_name"), item.get("canonical_path")]
            if any(norm(v) in token_set for v in searchable if v):
                ar_matches.append(item)
        for item in arxml_refs:
            if not isinstance(item, dict): continue
            if norm(item.get("reference")) in token_set:
                ar_matches.append(item)
        # De-duplicate identical candidate artifacts while preserving their source location.
        unique_ar, seen_ar = [], set()
        for item in ar_matches:
            marker = (item.get("file"), item.get("xpath"), item.get("canonical_path"), item.get("reference"))
            if marker not in seen_ar:
                seen_ar.add(marker); unique_ar.append(item)
        if not unique_ar:
            findings.append({"id": f"GAP-{len(findings)+1:04d}", "classification": "traceability_gap",
                             "severity": "warning", "net_id": net_id, "signal": net_name,
                             "gap": "no_exact_name_match_in_arxml_index",
                             "next_step": "Search configuration by verified signal/peripheral aliases; do not infer from similar names."})
        for index, item in enumerate(unique_ar):
            aid = f"arxml:{item.get('file')}:{item.get('xpath') or item.get('canonical_path') or item.get('reference')}"
            nodes.append({"id": aid, "type": "arxml_candidate", **item})
            edges.append({"from": nid, "to": aid, "relation": "exact_name_candidate",
                          "evidence": [{"file": item.get("file"), "xpath": item.get("xpath"), "canonical_path": item.get("canonical_path")}],
                          "review_state": "candidate_unverified",
                          "warning": "Exact name match only; validate ECUC semantics and release-specific configuration."})
        src_matches = []
        for hit in source_hits:
            if not isinstance(hit, dict): continue
            searchable = [hit.get("term"), hit.get("matched_text"), hit.get("symbol"), hit.get("line_text"), hit.get("path")]
            if any(norm(v) in token_set for v in searchable if v):
                src_matches.append(hit)
        if not src_matches:
            findings.append({"id": f"GAP-{len(findings)+1:04d}", "classification": "traceability_gap",
                             "severity": "info", "net_id": net_id, "signal": net_name,
                             "gap": "no_exact_name_match_in_source_search_results",
                             "next_step": "Search code with confirmed net aliases, MCAL APIs and IoHwAb/SWC symbols."})
        for item in src_matches:
            sid = f"source:{item.get('path') or item.get('file')}:{item.get('line') or item.get('line_number')}:{item.get('symbol') or item.get('term')}"
            nodes.append({"id": sid, "type": "source_candidate", **item})
            edges.append({"from": nid, "to": sid, "relation": "exact_name_candidate",
                          "evidence": [{"path": item.get("path") or item.get("file"), "line": item.get("line") or item.get("line_number"), "symbol": item.get("symbol")}],
                          "review_state": "candidate_unverified",
                          "warning": "Text match is not proof of call flow, runtime data flow or hardware behavior."})
    layers = {
        "ECUC": ["ECUC", "ECUC-MODULE-CONFIGURATION-VALUES", "ECUC-CONTAINER-VALUE", "ECUC-NUMERICAL-PARAM-VALUE", "ECUC-TEXTUAL-PARAM-VALUE"],
        "MCAL": ["DIO", "ADC", "PWM", "PORT", "SPI", "CAN", "ICU", "GPT"],
        "IoHwAb": ["IOHWAB", "IO-HARDWARE-ABSTRACTION"],
        "RTE": ["RTE", "RTE-EVENT", "RTE-EVENT-TO-RUNNABLE-MAPPING"],
        "SWC": ["APPLICATION-SW-COMPONENT", "SWC", "RUNNABLE-ENTITY", "PORT-PROTOTYPE", "VARIABLE-DATA-PROTOTYPE"]
    }
    for node in nodes:
        if node.get("type") != "arxml_candidate": continue
        text_value = " ".join(str(node.get(k, "")) for k in ("tag", "short_name", "canonical_path", "definition_ref")).upper()
        node["candidate_layer_tags"] = [layer for layer, tokens in layers.items() if any(t in text_value for t in tokens)]
        if not node["candidate_layer_tags"]:
            node["candidate_layer_tags"] = ["unclassified"]
    return {
        "schema_version": "1.0", "report_type": "schematic_to_autosar_candidate_trace",
        "analysis_only": True, "human_confirmation_required": True,
        "summary": {"nets": len(nets), "pins": len(pins), "nodes": len(nodes), "edges": len(edges), "findings": len(findings)},
        "nodes": nodes, "edges": edges, "findings": findings,
        "limitations": [
            "Only exact normalized name matches are proposed; aliases and indirect mappings may be missed.",
            "An exact name match is not proof of electrical connectivity, ECUC semantics, runtime data flow or software behavior.",
            "MCAL/IoHwAb/RTE/SWC labels are candidate classification based on names/tags, not validated AUTOSAR semantics.",
            "Missing inputs are reported as gaps; no data is fabricated."
        ]
    }

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inventory_json", type=Path)
    parser.add_argument("--arxml-index", type=Path)
    parser.add_argument("--source-hits", type=Path)
    parser.add_argument("--out", type=Path, default=Path("engineering/traceability/hardware_code_trace.json"))
    args = parser.parse_args()
    try:
        inventory = load_object(args.inventory_json)
        arxml = load_object(args.arxml_index) if args.arxml_index else None
        source = load_object(args.source_hits) if args.source_hits else None
        report = build_graph(inventory, arxml, source)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Nets={report['summary']['nets']} nodes={report['summary']['nodes']} edges={report['summary']['edges']} findings={report['summary']['findings']}")
        print(f"Output: {args.out}")
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Trace graph failed: {exc}")
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
