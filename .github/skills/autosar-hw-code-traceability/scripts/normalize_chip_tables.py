#!/usr/bin/env python3
"""Normalize candidate chip-manual tables into reviewable pin/register/electrical records.

Header-based extraction only. Every record retains its raw row, page and source hash;
unmapped or ambiguous cells remain visible and no value is considered verified.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ALIASES = {
    "pin_number": ("pin number", "pin no", "pin #", "terminal", "ball number", "ball"),
    "pin_name": ("pin name", "signal name", "terminal name", "pin"),
    "pin_function": ("pin description", "function", "alternate function", "signal function"),
    "register_name": ("register name", "register", "peripheral register"),
    "offset": ("offset", "address offset", "register offset"),
    "address": ("base address", "address"),
    "reset_value": ("reset value", "reset", "default value"),
    "access": ("access", "access type", "r/w", "read/write"),
    "bit_field": ("bit field", "field", "bits", "bit position"),
    "parameter": ("parameter", "characteristic", "symbol"),
    "minimum": ("min", "minimum"),
    "typical": ("typ", "typical"),
    "maximum": ("max", "maximum"),
    "unit": ("unit", "units"),
    "conditions": ("conditions", "test conditions", "condition"),
}


def norm_header(value: Any) -> str:
    value = "" if value is None else str(value).lower()
    return re.sub(r"[^a-z0-9#/+]+", " ", value).strip()


def map_headers(headers: list[Any]) -> dict[str, int]:
    mapped: dict[str, int] = {}
    normalized = [norm_header(x) for x in headers]
    for field, aliases in ALIASES.items():
        candidates = [norm_header(alias) for alias in aliases]
        matches = [i for i, name in enumerate(normalized) if name and any(name == alias or (len(alias) > 4 and alias in name) for alias in candidates)]
        if len(matches) == 1:
            mapped[field] = matches[0]
    return mapped


def cell(row: list[Any], index: int | None) -> Any:
    if index is None or index >= len(row):
        return None
    return row[index]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tables_json", type=Path, help="Output JSON from extract_chip_tables.py")
    parser.add_argument("--out", type=Path, default=Path("engineering/chip_manual/chip_manual_review_records.json"))
    args = parser.parse_args()
    if not args.tables_json.is_file():
        parser.error(f"Input JSON not found: {args.tables_json}")
    try:
        source = json.loads(args.tables_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        parser.error(f"Could not read input JSON: {exc}")
    if not isinstance(source, dict) or not isinstance(source.get("tables"), list):
        parser.error("Input must be a chip table extraction report containing a tables array.")

    records: list[dict[str, Any]] = []
    table_summaries = []
    for table in source["tables"]:
        if not isinstance(table, dict):
            continue
        rows = table.get("rows") or []
        if not isinstance(rows, list) or not rows:
            continue
        header = table.get("header") if isinstance(table.get("header"), list) and table.get("header") else rows[0]
        mapping = map_headers(header)
        # PyMuPDF table extraction includes the first row in rows; skip it as the header.
        start = 1
        if not mapping:
            table_summaries.append({
                "table_id": table.get("table_id"),
                "pdf_page": table.get("pdf_page"),
                "status": "unmapped_headers",
                "header": header,
                "reason": "No unique recognized column headers; retain raw table and review manually.",
            })
            continue
        topic_list = table.get("candidate_topics") or []
        if "pinout" in topic_list or "pin_mux" in topic_list or "pin_number" in mapping or "pin_name" in mapping:
            record_type = "pin_candidate"
        elif "registers" in topic_list or "register_name" in mapping or "offset" in mapping:
            record_type = "register_candidate"
        elif "electrical_limits" in topic_list or "parameter" in mapping or "minimum" in mapping or "maximum" in mapping:
            record_type = "electrical_candidate"
        elif "timing" in topic_list:
            record_type = "timing_candidate"
        else:
            record_type = "generic_candidate"

        count = 0
        for row_index, row in enumerate(rows[start:], start=start + 1):
            if not isinstance(row, list) or not any(x not in (None, "") for x in row):
                continue
            values = {field: cell(row, index) for field, index in mapping.items()}
            records.append({
                "record_id": f"{table.get('table_id', 'table')}-row-{row_index}",
                "record_type": record_type,
                "source_table_id": table.get("table_id"),
                "pdf_page": table.get("pdf_page"),
                "document_sha256": (table.get("evidence") or {}).get("document_sha256"),
                "header_mapping": mapping,
                "values": values,
                "raw_row": row,
                "review_status": "unreviewed",
                "confidence": "low",
                "requires_source_page_verification": True,
            })
            count += 1
        table_summaries.append({
            "table_id": table.get("table_id"),
            "pdf_page": table.get("pdf_page"),
            "status": "mapped_candidate_rows" if count else "no_data_rows",
            "record_type": record_type,
            "header_mapping": mapping,
            "records_created": count,
        })

    args.out.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "schema_version": "1.0",
        "source_report": str(args.tables_json),
        "document": source.get("document", {}),
        "records_created": len(records),
        "records": records,
        "table_review_summary": table_summaries,
        "limitations": [
            "Column mapping uses header aliases and does not understand all vendor-specific terminology.",
            "Merged cells, multi-row headers, repeated headers, footnotes and table continuations may require manual correction.",
            "Rows are candidates only; confirm every field against the cited original PDF page before engineering use.",
            "No device/package matching, electrical interpretation, unit conversion or register-address calculation is performed.",
            "Unknown or ambiguous columns are preserved in raw_row and must not be silently discarded.",
        ],
    }
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Review records: {len(records)}; tables summarized: {len(table_summaries)}")
    print(f"Review JSON: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
