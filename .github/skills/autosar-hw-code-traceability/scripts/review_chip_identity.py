#!/usr/bin/env python3
"""Compare chip-manual identity candidates with a project manifest without auto-approving matches.

This is a review aid. Candidate extraction is label-based and deliberately conservative.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

FIELD_PATTERNS = {
    "part_number": [
        re.compile(r"\b(?:ordering\s+(?:part\s+)?number|orderable\s+part(?:\s+number)?|part\s+number|device\s+ordering\s+code|order\s+code)\s*[:#=\-]?\s*([A-Z0-9][A-Z0-9._/+\-]{3,})", re.I),
    ],
    "package": [
        re.compile(r"\b(?:package(?:\s+type)?|package\s+option|package\s+code)\s*[:#=\-]?\s*([A-Z0-9][A-Z0-9._/+\-]{1,})", re.I),
    ],
    "datasheet_revision": [
        re.compile(r"\b(?:document\s+revision|datasheet\s+revision|revision|rev\.)\s*[:#=\-]?\s*(?:revision\s*)?([A-Z0-9][A-Z0-9._/+\-]{0,15})", re.I),
    ],
    "silicon_revision": [
        re.compile(r"\b(?:silicon\s+revision|device\s+revision|mask\s+set|stepping)\s*[:#=\-]?\s*([A-Z0-9][A-Z0-9._/+\-]{0,15})", re.I),
    ],
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical(value: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


def extract_candidates(report: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    found: dict[str, list[dict[str, Any]]] = {field: [] for field in FIELD_PATTERNS}
    pages = report.get("pages", [])
    for page in pages if isinstance(pages, list) else []:
        if not isinstance(page, dict):
            continue
        page_no = page.get("pdf_page")
        content = str(page.get("text") or page.get("evidence_snippet") or "")
        for field, patterns in FIELD_PATTERNS.items():
            for pattern in patterns:
                for match in pattern.finditer(content):
                    value = match.group(1).strip(" .,:;()[]{}")
                    if not value or len(value) > 80:
                        continue
                    item = {"value": value, "pdf_page": page_no,
                            "evidence_excerpt": content[max(0, match.start()-100):min(len(content), match.end()+100)].replace("\n", " ").strip(),
                            "status": "unconfirmed"}
                    key = (canonical(value), page_no)
                    if not any((canonical(x["value"]), x["pdf_page"]) == key for x in found[field]):
                        found[field].append(item)
    return found


def load_manifest(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("components"), list):
        components = data["components"]
    elif isinstance(data, list):
        components = data
    else:
        raise ValueError("Manifest must be a JSON array or an object with a components array.")
    if not all(isinstance(x, dict) for x in components):
        raise ValueError("Every manifest component must be a JSON object.")
    return components


def compare(expected: Any, candidates: list[dict[str, Any]]) -> dict[str, Any]:
    if expected in (None, ""):
        status = "manifest_value_missing"
    elif not candidates:
        status = "no_manual_candidate_found"
    elif any(canonical(expected) == canonical(x["value"]) for x in candidates):
        status = "candidate_exact_match_unconfirmed"
    else:
        status = "candidate_mismatch_review_required"
    return {"manifest_value": expected, "manual_candidates": candidates, "status": status,
            "human_confirmation_required": True}


def build_report(analysis: dict[str, Any], manifest: list[dict[str, Any]], source_path: str) -> dict[str, Any]:
    candidates = extract_candidates(analysis)
    document = analysis.get("document") if isinstance(analysis.get("document"), dict) else {}
    checks = []
    fields = ("part_number", "package", "datasheet_revision", "silicon_revision")
    if manifest:
        for component in manifest:
            checks.append({
                "reference": component.get("reference") or component.get("ref"),
                "manufacturer": component.get("manufacturer"),
                "checks": {field: compare(component.get(field), candidates[field]) for field in fields},
                "component_status": "unconfirmed_review_required",
            })
    else:
        checks.append({
            "reference": None,
            "checks": {field: compare(None, candidates[field]) for field in fields},
            "component_status": "manifest_not_provided_manual_candidates_only",
        })
    gaps = []
    for field in fields:
        if not candidates[field]:
            gaps.append({"field": field, "reason": "No conservatively label-matched candidate found; inspect cover, ordering table and revision history."})
    if not manifest:
        gaps.append({"field": "project_manifest", "reason": "No BOM/device manifest supplied; project applicability cannot be checked."})
    return {
        "schema_version": "1.0",
        "report_type": "chip_identity_review",
        "source_analysis": source_path,
        "document": {
            "file": document.get("file"),
            "sha256": document.get("sha256"),
            "pdf_page_count": document.get("pdf_page_count"),
            "metadata": document.get("metadata", {}),
        },
        "candidate_extraction_method": "conservative_label_regex_over_extracted_page_text",
        "manual_candidates": candidates,
        "component_checks": checks,
        "review_gaps": gaps,
        "decision": "unconfirmed",
        "limitations": [
            "This report does not establish that the manual applies to the fitted component.",
            "Exact string equality is only a candidate match; ordering suffixes, package variants and silicon applicability require human confirmation.",
            "Only explicitly labelled nearby text is searched; tables, cover-page layouts and vendor-specific labels may not be recognized.",
            "No OCR, fuzzy matching, part-number inference or package inference is performed.",
            "Confirm the full ordering code, package, datasheet revision, silicon revision and applicable errata against the original source and project BOM.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("analysis_json", type=Path, help="Output JSON from analyze_chip_manual.py")
    parser.add_argument("--manifest", type=Path, help="Optional BOM/device manifest JSON")
    parser.add_argument("--out", type=Path, default=Path("engineering/chip_manual/chip_identity_review.json"))
    args = parser.parse_args()
    if not args.analysis_json.is_file():
        parser.error(f"Analysis JSON not found: {args.analysis_json}")
    if args.analysis_json.suffix.lower() != ".json":
        parser.error("analysis_json must be a .json file.")
    if args.manifest is not None and (not args.manifest.is_file() or args.manifest.suffix.lower() != ".json"):
        parser.error("--manifest must point to an existing .json file.")
    try:
        analysis = json.loads(args.analysis_json.read_text(encoding="utf-8"))
        if not isinstance(analysis, dict) or not isinstance(analysis.get("pages"), list):
            raise ValueError("analysis input must contain a pages array.")
        manifest = load_manifest(args.manifest)
        report = build_report(analysis, manifest, str(args.analysis_json))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))
    report["source_analysis_sha256"] = sha256(args.analysis_json)
    if args.manifest:
        report["manifest_file"] = str(args.manifest)
        report["manifest_sha256"] = sha256(args.manifest)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Identity review: {len(report['manual_candidates'])} fields scanned; component checks: {len(report['component_checks'])}; decision: unconfirmed")
    print(f"Review JSON: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
