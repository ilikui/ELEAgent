#!/usr/bin/env python3
"""Generate a human-review Markdown report from a traceability JSON file."""
import argparse
import json
from pathlib import Path

def display(value):
    if value is None or value == "":
        return "UNKNOWN"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--out", type=Path, default=Path("engineering/reports/review_report.md"))
    args = parser.parse_args()
    data = json.loads(args.file.read_text(encoding="utf-8"))
    if data.get("report_type") == "schematic_to_autosar_candidate_trace":
        nodes = data.get("nodes", [])
        edges = data.get("edges", [])
        findings = data.get("findings", [])
        lines = [
            "# Schematic-to-AUTOSAR Candidate Trace Review", "",
            f"- Nets: {display(data.get('summary', {}).get('nets'))}",
            f"- Nodes: {display(data.get('summary', {}).get('nodes'))}",
            f"- Candidate edges: {display(data.get('summary', {}).get('edges'))}",
            f"- Findings/gaps: {display(data.get('summary', {}).get('findings'))}",
            "- Status: analysis only; all name matches remain candidates.", "",
            "> Exact-name matches do not prove electrical connectivity, ECUC semantics, runtime data flow or safety behavior.", "",
            "## Trace candidates", ""
        ]
        for edge in edges:
            if not isinstance(edge, dict): continue
            lines += [f"### {display(edge.get('relation'))}", "",
                      f"- From: {display(edge.get('from'))}",
                      f"- To: {display(edge.get('to'))}",
                      f"- Review state: {display(edge.get('review_state'))}"]
            if edge.get("warning"): lines.append(f"- Warning: {display(edge.get('warning'))}")
            lines += [f"- Evidence: {display(edge.get('evidence'))}", ""]
        lines += ["## Findings and broken links", ""]
        if findings:
            for finding in findings:
                if not isinstance(finding, dict): continue
                lines += [f"### {display(finding.get('id'))}: {display(finding.get('gap'))}", "",
                          f"- Classification/severity: {display(finding.get('classification'))} / {display(finding.get('severity'))}",
                          f"- Net/signal: {display(finding.get('net_id'))} / {display(finding.get('signal'))}",
                          f"- Next step: {display(finding.get('next_step'))}", ""]
        else:
            lines.append("- No gaps emitted by this heuristic run; this is not proof of completeness.")
        lines += ["## Candidate layer coverage", ""]
        for layer in ("ECUC", "MCAL", "IoHwAb", "RTE", "SWC"):
            matches = [node for node in nodes if isinstance(node, dict) and node.get("type") == "arxml_candidate" and layer in node.get("candidate_layer_tags", [])]
            lines.append(f"- {layer}: {len(matches)} candidate ARXML node(s)")
        lines += ["", "## Approval gate", "",
                  "Review each edge against the controlled schematic, exact chip/package/manual, ECUC release-specific configuration, generated-code origin, source call/data flow and verification evidence. Do not treat candidate matches as approved traceability.", ""]
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text("\\n".join(lines), encoding="utf-8")
        print(f"Report written: {args.out}")
        return 0
    records = data.get("records", [])
    lines = [
        "# Hardware-to-AUTOSAR Traceability Review", "",
        f"- Project: {display(data.get('project'))}",
        f"- Schema version: {display(data.get('schema_version'))}",
        f"- Records: {len(records)}",
        "- Mode: analysis only; this report does not authorize changes.", "",
        "> Automated output is a review aid. Confirm schematic connectivity, chip documentation, ARXML semantics and safety-related behavior against controlled source artifacts.", ""
    ]
    unresolved = []
    for record in records:
        rid = display(record.get("id"))
        lines += [f"## {rid}", "", f"- Status: {display(record.get('status'))}",
                  f"- Confidence: {display(record.get('confidence'))}"]
        for group in ("requirement", "hardware", "chip", "autosar", "software", "verification"):
            value = record.get(group, {})
            serialized = json.dumps(value, ensure_ascii=False).casefold()
            lines += [f"- {group.title()}: {display(value)}"]
            if "unknown" in serialized or "unverified" in serialized or "needs_human_review" in serialized:
                unresolved.append((rid, group))
        questions = record.get("open_questions", [])
        lines += ["", "### Open questions", ""]
        if questions:
            lines.extend(f"- {question}" for question in questions)
        else:
            lines.append("- None recorded; reviewer should still verify evidence completeness.")
        lines.append("")
    lines += ["## Review summary", "", f"- Records with unresolved group data: {len(set(rid for rid, _ in unresolved))}"]
    lines.extend(f"- {rid}: review {group} evidence" for rid, group in unresolved)
    lines += ["", "## Approval gate", "",
              "No source, ARXML, ECUC configuration or generated file should be modified until the owner approves a concrete plan listing exact files, rationale, risks and verification steps.", ""]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report written: {args.out}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
