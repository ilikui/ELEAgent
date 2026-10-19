#!/usr/bin/env python3
"""Extract selectable PDF text by page and optionally render page images."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--out", type=Path, default=Path("engineering/extracted/pdf_text"))
    parser.add_argument("--min-chars", type=int, default=40)
    parser.add_argument("--render", action="store_true")
    args = parser.parse_args()
    if not args.pdf.is_file():
        parser.error(f"PDF not found: {args.pdf}")
    try:
        import fitz
    except ImportError:
        print("Missing dependency. Install with: python -m pip install pymupdf", file=sys.stderr)
        return 2
    args.out.mkdir(parents=True, exist_ok=True)
    image_dir = args.out.parent / "page_images" / args.pdf.stem
    if args.render:
        image_dir.mkdir(parents=True, exist_ok=True)
    pages, review_pages = [], []
    with fitz.open(args.pdf) as document:
        for index, page in enumerate(document, start=1):
            text = page.get_text("text")
            (args.out / f"{args.pdf.stem}_page_{index:04d}.txt").write_text(text, encoding="utf-8")
            low_text = len(text.strip()) < args.min_chars
            pages.append({"page": index, "chars": len(text.strip()), "needs_visual_review": low_text})
            if low_text:
                review_pages.append(index)
            if args.render:
                page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False).save(image_dir / f"page_{index:04d}.png")
        manifest = {
            "file": str(args.pdf), "sha256": sha256(args.pdf),
            "page_count": len(document), "metadata": document.metadata,
            "pages": pages, "review_pages": review_pages,
            "limitations": [
                "Low text count is a heuristic, not proof that a page is scanned.",
                "OCR, net connectivity interpretation and human visual review are not performed.",
                "PDF metadata may not reliably identify the controlled document revision."
            ]
        }
    manifest_path = args.out / f"{args.pdf.stem}_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Pages: {len(pages)}; pages flagged for visual review: {review_pages}")
    print(f"Manifest: {manifest_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
