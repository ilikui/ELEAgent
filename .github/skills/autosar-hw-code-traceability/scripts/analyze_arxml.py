#!/usr/bin/env python3
"""Build a cross-file ARXML name/reference index. Not a vendor AUTOSAR validator."""
import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

def lname(tag):
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag

def direct_text(node, name):
    for child in list(node):
        if lname(child.tag) == name and child.text:
            return child.text.strip()
    return None

def iter_arxml(root):
    if root.is_file():
        return [root] if root.suffix.lower() == ".arxml" else []
    return sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() == ".arxml")

def collect_paths(node, parent_path, file_name, elements, refs, xpath):
    short_name = direct_text(node, "SHORT-NAME")
    canonical = f"{parent_path}/{short_name}" if short_name else parent_path
    tag = lname(node.tag)
    if short_name:
        elements.append({
            "file": file_name, "tag": tag, "short_name": short_name,
            "canonical_path": canonical or None,
            "xpath": xpath,
            "definition_ref": direct_text(node, "DEFINITION-REF")
        })
    sibling_counts = {}
    for child in list(node):
        child_tag = lname(child.tag)
        sibling_counts[child_tag] = sibling_counts.get(child_tag, 0) + 1
        child_xpath = f"{xpath}/{child_tag}[{sibling_counts[child_tag]}]"
        if child.text and child.text.strip() and (child_tag.endswith("-REF") or child_tag.endswith("-TREF")):
            refs.append({
                "file": file_name, "tag": child_tag, "xpath": child_xpath,
                "reference": child.text.strip(), "dest": child.attrib.get("DEST"),
                "owner_tag": tag, "owner_short_name": short_name,
                "owner_path": canonical or None, "owner_xpath": xpath
            })
    sibling_counts = {}
    for child in list(node):
        child_tag = lname(child.tag)
        sibling_counts[child_tag] = sibling_counts.get(child_tag, 0) + 1
        if child_tag == "SHORT-NAME":
            continue
        child_xpath = f"{xpath}/{child_tag}[{sibling_counts[child_tag]}]"
        collect_paths(child, canonical, file_name, elements, refs, child_xpath)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="ARXML file or directory")
    parser.add_argument("--out", type=Path, default=Path("engineering/traceability/arxml_analysis.json"))
    parser.add_argument("--max-bytes", type=int, default=50_000_000)
    args = parser.parse_args()
    if not args.root.exists():
        parser.error(f"Path not found: {args.root}")
    files = iter_arxml(args.root)
    elements, refs, errors, namespaces = [], [], [], []
    for file in files:
        try:
            if file.stat().st_size > args.max_bytes:
                errors.append({"file": file.as_posix(), "error": "skipped: exceeds --max-bytes"})
                continue
            root = ET.parse(file).getroot()
        except (OSError, ET.ParseError) as exc:
            errors.append({"file": file.as_posix(), "error": str(exc)})
            continue
        namespace = root.tag[1:].split("}", 1)[0] if root.tag.startswith("{") else None
        namespaces.append({"file": file.as_posix(), "namespace": namespace})
        root_xpath = f"/{lname(root.tag)}[1]"
        collect_paths(root, "", file.as_posix(), elements, refs, root_xpath)

    path_index = {}
    for item in elements:
        path = item.get("canonical_path")
        if path:
            path_index.setdefault(path, []).append(item)
    for ref in refs:
        targets = path_index.get(ref["reference"], [])
        ref["resolution"] = "resolved_unique" if len(targets) == 1 else (
            "unresolved" if not targets else "ambiguous_multiple_targets")
        ref["target_candidates"] = [
            {"file": target["file"], "tag": target["tag"], "short_name": target["short_name"],
             "xpath": target["xpath"]}
            for target in targets
        ]

    output = {
        "schema_version": "1.1", "input": args.root.as_posix(),
        "files": namespaces, "element_count": len(elements), "reference_count": len(refs),
        "elements": elements, "references": refs, "errors": errors,
        "limitations": [
            "Reference matching uses indexed SHORT-NAME paths and is heuristic; supplier-specific reference rules and variants may need normalization.",
            "Generated XPath strings are namespace-agnostic location hints, not schema-aware identifiers; verify them against the original XML.",
            "No AUTOSAR XSD validation, ECUC semantic validation, variant resolution, or generator validation is performed.",
            "Canonical paths are candidate evidence and must be checked against source ARXML before being used in a safety-related finding."
        ]
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    resolved = sum(1 for ref in refs if ref["resolution"] == "resolved_unique")
    unresolved = sum(1 for ref in refs if ref["resolution"] == "unresolved")
    ambiguous = sum(1 for ref in refs if ref["resolution"] == "ambiguous_multiple_targets")
    print(f"Files={len(namespaces)} elements={len(elements)} references={len(refs)} unique={resolved} unresolved={unresolved} ambiguous={ambiguous} errors={len(errors)}")
    print(f"Output: {args.out}")
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(main())
