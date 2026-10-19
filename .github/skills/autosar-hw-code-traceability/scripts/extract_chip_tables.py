#!/usr/bin/env python3
"""Extract candidate tables from chip-manual PDFs with page-level provenance.

PyMuPDF's table detector is heuristic. Output is candidate data for review, not a
validated pin/register/electrical specification.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

TABLE_TOPICS = {
    "pinout": ("pin number", "pin no", "pin name", "terminal", "ball", "signal name", "pin description"),
    "pin_mux": ("alternate function", "mux", "af0", "af1", "gpio", "function"),
    "registers": ("register", "offset", "address", "reset value", "bit", "field", "access"),
    "electrical_limits": ("parameter", "symbol", "min", "typ", "max", "unit", "conditions", "vih", "vil", "voh", "vol"),
    "timing": ("setup", "hold", "rise time", "fall time", "frequency", "period", "timing"),
    "ordering_package": ("ordering", "package", "part number", "order code", "device"),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clean_cell(value: Any) -> str | None:
    if value is None:
        return None
    value = re.sub(r"\s+", " ", str(value)).strip()
    return value or None


def classify_table(rows: list[list[str | None]]) -> list[str]:
    sample = " ".join(cell or "" for row in rows[:4] for cell in row).lower()
    return [
        topic for topic, terms in TABLE_TOPICS.items()
        if any(term in sample for term in terms)
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path, help="Chip datasheet/reference manual/errata PDF")
    parser.add_argument("--out", type=Path, default=Path("engineering/chip_manual/chip_manual_tables.json"))
    parser.add_argument("--min-rows", type=int, default=2)
    args = parser.parse_args()
    if not args.pdf.is_file():
        parser.error(f"PDF not found: {args.pdf}")
    if args.pdf.suffix.lower() != ".pdf":
        parser.error("Input must be a PDF file.")
    if not 1 <= args.min_rows <= 10000:
        parser.error("--min-rows must be between 1 and 10000")
    try:
        import fitz
    except ImportError:
        print("Missing dependency. Install with: python -m pip install pymupdf", file=sys.stderr)
        return 2

    tables: list[dict[str, Any]] = []
    review_pages: list[dict[str, Any]] = []
    with fitz.open(args.pdf) as doc:
        page_count = len(doc)
        metadata = doc.metadata or {}
        for page_number, page in enumerate(doc, start=1):
            page_text = (page.get_text("text") or "").strip()
            try:
                finder = page.find_tables()
            except (AttributeError, TypeError, RuntimeError) as exc:
                review_pages.append({
                    "pdf_page": page_number,
                    "reason": f"table_detector_unavailable_or_failed: {type(exc).__name__}",
                    "character_count": len(page_text),
                })
                continue

            found_count = 0
            for local_index, table in enumerate(finder.tables, start=1):
                try:
                    extracted = table.extract()
                except Exception as exc:
                    review_pages.append({
                        "pdf_page": page_number,
                        "reason": f"table_extraction_failed: {type(exc).__name__}",
                        "table_index": local_index,
                    })
                    continue
                rows = [[clean_cell(cell) for cell in row] for row in (extracted or [])]
                rows = [row for row in rows if any(cell is not None for cell in row)]
                if len(rows) < args.min_rows:
                    continue
                header = getattr(table, "header", None)
                header_names = []
                if header is not None:
                    try:
                        header_names = [clean_cell(x) for x in (header.names or [])]
                    except Exception:
                        header_names = []
                bbox = getattr(table, "bbox", None)
                found_count += 1
                tables.append({
                    "table_id": f"pdf-page-{page_number}-table-{local_index}",
                    "pdf_page": page_number,
                    "printed_page_label": None,
                    "bbox": [round(float(v), 2) for v in bbox] if bbox else None,
                    "row_count": len(rows),
                    "column_count_max": max((len(row) for row in rows), default=0),
                    "header": header_names,
                    "candidate_topics": classify_table(rows),
                    "rows": rows,
                    "extraction_method": "pymupdf_find_tables",
                    "confidence": "medium",
                    "review_status": "unreviewed",
                    "needs_manual_review": True,
                    "evidence": {
                        "pdf_file": str(args.pdf),
                        "pdf_page": page_number,
                        "document_sha256": None,
                    },
                })
            if found_count == 0:
                review_pages.append({
                    "pdf_page": page_number,
                    "reason": "no_table_detected; this does_not_prove_no_table_exists",
                    "character_count": len(page_text),
                    "low_text_page": len(page_text) < 80,
                })

    digest = sha256(args.pdf)
    for item in tables:
        item["evidence"]["document_sha256"] = digest
    args.out.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "schema_version": "1.0",
        "document": {
            "file": str(args.pdf),
            "sha256": digest,
            "pdf_page_count": page_count,
            "metadata": metadata,
        },
        "tables_found": len(tables),
        "tables": tables,
        "pages_requiring_review": review_pages,
        "limitations": [
            "Detected tables are candidates, not validated specifications.",
            "Merged cells, split tables, footnotes, multi-level headers and row/column alignment may be wrong.",
            "Candidate topic labels are keyword-based and do not establish technical meaning.",
            "No OCR is performed for scanned/image-only tables.",
            "Verify every consequential value against the rendered source page before using it for design or code.",
        ],
    }
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Candidate tables: {len(tables)}; pages requiring review: {len(review_pages)}")
    print(f"Table extraction JSON: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
