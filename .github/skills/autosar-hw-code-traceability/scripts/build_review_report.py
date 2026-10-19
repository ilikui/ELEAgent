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
