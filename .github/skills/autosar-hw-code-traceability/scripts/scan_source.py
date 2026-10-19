#!/usr/bin/env python3
"""Search source/configuration text. Matches are discovery hints, not semantic proof."""
import argparse
import json
from pathlib import Path

EXTENSIONS = {".c", ".h", ".cpp", ".hpp", ".arxml", ".xml", ".yaml", ".yml", ".json", ".cfg", ".txt", ".inc"}
SKIP_DIRS = {".git", ".svn", ".venv", "venv", "node_modules", "build", "out", "debug", "release"}

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--terms", required=True, help="Comma-separated terms")
    parser.add_argument("--out", type=Path, default=Path("engineering/traceability/source_hits.json"))
    parser.add_argument("--max-bytes", type=int, default=5_000_000)
    args = parser.parse_args()
    if not args.root.is_dir():
        parser.error(f"Root directory not found: {args.root}")
    terms = [term.strip() for term in args.terms.split(",") if term.strip()]
    results = []
    for path in args.root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in EXTENSIONS:
            continue
        if any(part.lower() in SKIP_DIRS for part in path.parts):
            continue
        try:
            if path.stat().st_size > args.max_bytes:
                continue
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for line_number, line in enumerate(lines, 1):
            matched = [term for term in terms if term.casefold() in line.casefold()]
            if matched:
                results.append({
                    "file": path.as_posix(), "line": line_number,
                    "terms": matched, "text": line.strip()[:1000],
                    "evidence_kind": "text_match_not_semantic_proof"
                })
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({
        "root": args.root.as_posix(), "terms": terms, "match_count": len(results),
        "matches": results,
        "limitations": ["No call graph resolution.", "No ARXML reference resolution.", "No proof of hardware connectivity."]
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(results)} matches written to {args.out}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
