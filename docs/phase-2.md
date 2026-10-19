# Phase 2: structured AUTOSAR discovery

This increment adds a cross-file ARXML reference index and a Markdown review report.

## ARXML analyzer
The script analyze_arxml.py records SHORT-NAME-bearing elements, candidate canonical paths, reference text, DEST attributes, and heuristic cross-file resolution states:
- resolved_unique
- unresolved
- ambiguous_multiple_targets

These are discovery statuses, not definitive AUTOSAR validity outcomes. Variant conditions, supplier extensions, schema constraints, and ECUC semantics are not fully interpreted. Use the correct AUTOSAR XSD and the project's vendor configurator/validator for authoritative results.

## Review report
The script build_review_report.py turns a reviewed traceability.json into Markdown. It never edits application code or grants approval.

## Commands
```bash
python .github/skills/autosar-hw-code-traceability/scripts/analyze_arxml.py path/to/arxml --out engineering/traceability/arxml_analysis.json
python .github/skills/autosar-hw-code-traceability/scripts/build_review_report.py examples/traceability.example.json --out engineering/reports/review_report.md
python -m unittest discover -s tests -v
```

## Acceptance boundary
Passing these tests proves only that the sample scripts behave as tested on synthetic inputs. It does not prove correctness against a production AUTOSAR release, vendor ARXML, target compiler, ECU hardware or vehicle.
