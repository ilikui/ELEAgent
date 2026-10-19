#!/usr/bin/env python3
"""Build a page-cited topic/evidence index for a semiconductor manual PDF.

This is a retrieval aid, not a complete datasheet table parser or an electrical sign-off.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

TOPICS = {
    "device_identity": ["ordering information", "orderable part", "device summary", "part number", "package options"],
    "pinout": ["pinout", "pin assignment", "pin description", "pin functions", "terminal functions", "ball assignment"],
    "pin_mux": ["alternate function", "alternate functions", "multiplex", "pin mux", "afsel", "port mux", "signal multiplexing"],
    "electrical_limits": ["absolute maximum", "recommended operating conditions", "electrical characteristics", "input leakage", "voh", "vol", "vih", "vil"],
    "power_reset_clock": ["power sequencing", "power supply", "power-up", "reset timing", "clock characteristics", "oscillator", "boot configuration"],
    "registers": ["register map", "register summary", "register description", "memory map", "bit field", "reset value", "register offset"],
    "timing": ["timing characteristics", "switching characteristics", "setup time", "hold time", "timing diagram", "bus timing"],
    "peripherals": ["gpio", "analog-to-digital converter", "adc", "flexcan", "can controller", "lin", "spi", "i2c", "uart", "dma", "watchdog"],
    "errata": ["errata", "silicon limitation", "known issue", "workaround"],
    "safety_security": ["functional safety", "security", "secure boot", "lockstep", "watchdog", "safety manual"],
}
LOW_TEXT_CHARS = 80


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path, help="Chip datasheet/reference manual/errata PDF")
    parser.add_argument("--out", type=Path, default=Path("engineering/chip_manual/chip_manual_analysis.json"))
    parser.add_argument("--min-chars", type=int, default=LOW_TEXT_CHARS)
    args = parser.parse_args()
    if not args.pdf.is_file():
        parser.error(f"PDF not found: {args.pdf}")
    if args.pdf.suffix.lower() != ".pdf":
        parser.error("Input must be a PDF file.")
    if not 0 <= args.min_chars <= 100000:
        parser.error("--min-chars must be between 0 and 100000")
    try:
        import fitz
    except ImportError:
        print("Missing dependency. Install with: python -m pip install pymupdf", file=sys.stderr)
        return 2

    pages = []
    topic_pages: dict[str, list[int]] = {name: [] for name in TOPICS}
    low_text_pages = []
    with fitz.open(args.pdf) as doc:
        metadata = doc.metadata or {}
        for page_index, page in enumerate(doc, start=1):
            raw_text = page.get_text("text") or ""
            normalized = re.sub(r"\s+", " ", raw_text).strip()
            hits = []
            lowered = normalized.lower()
            for topic, terms in TOPICS.items():
                matched = [term for term in terms if term in lowered]
                if matched:
                    topic_pages[topic].append(page_index)
                    hits.append({"topic": topic, "matched_terms": matched})
            needs_review = len(normalized) < args.min_chars
            if needs_review:
                low_text_pages.append(page_index)
            pages.append({
                "pdf_page": page_index,
                "printed_page_label": None,
                "character_count": len(normalized),
                "needs_visual_review": needs_review,
                "topic_hits": hits,
                "evidence_snippet": normalized[:700] if normalized else "",
                "text": raw_text,
                "extraction_method": "pymupdf_selectable_text",
                "confidence": "medium" if normalized else "unknown",
            })

    args.out.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "schema_version": "1.0",
        "document": {
            "file": str(args.pdf),
            "sha256": sha256(args.pdf),
            "pdf_page_count": len(pages),
            "metadata": metadata,
            "controlled_revision": None,
            "device_ordering_code": None,
            "package": None,
        },
        "topic_index": [
            {"topic": topic, "pdf_pages": numbers, "matched_terms": TOPICS[topic]}
            for topic, numbers in topic_pages.items()
        ],
        "pages": pages,
        "review_gaps": {
            "low_text_pages": low_text_pages,
            "must_confirm_device_ordering_code_and_package": True,
            "must_check_errata_and_document_revision": True,
            "table_structure_and_footnote_alignment_verified": False,
        },
        "limitations": [
            "Keyword matching is a navigation aid; a hit does not establish a technical conclusion.",
            "Text extraction does not guarantee correct table row/column alignment or footnote association.",
            "Scanned/image-only pages are flagged by text length; OCR and visual inspection are not performed.",
            "Device ordering code, package and controlled revision must be confirmed against the document and project BOM.",
            "No electrical limits, pin assignments or register values are inferred or certified by this tool.",
        ],
    }
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    page_total = len(pages)
    topic_count = sum(bool(v) for v in topic_pages.values())
    print(f"Pages indexed: {page_total}; topics with matches: {topic_count}; pages needing visual review: {low_text_pages}")
    print(f"Analysis JSON: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
