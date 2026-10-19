# Getting started

## Requirements
- Python 3.10 or later.
- Install PDF dependency: python -m pip install -r requirements.txt
- Optional rendering uses PyMuPDF. OCR requires a separately installed OCR engine and a reviewed workflow.
- Vendor AUTOSAR configurator, compiler, license and project environment are separate requirements.

## Extract selectable PDF text and render pages for review
```bash
python .github/skills/autosar-hw-code-traceability/scripts/extract_pdf.py path/to/schematic.pdf --out engineering/extracted/pdf_text --render
```

## Inventory and analyze ARXML
```bash
python .github/skills/autosar-hw-code-traceability/scripts/inventory_arxml.py path/to/arxml --out engineering/traceability/arxml_inventory.json
python .github/skills/autosar-hw-code-traceability/scripts/analyze_arxml.py path/to/arxml --out engineering/traceability/arxml_analysis.json
```
The analyzer attempts heuristic cross-file reference matching. It is not a replacement for release-specific XSD validation or the vendor ECUC/configuration validator.

## Search source and configuration
```bash
python .github/skills/autosar-hw-code-traceability/scripts/scan_source.py . --terms "CONFIRMED_NET_NAME,Dio_WriteChannel,Rte_Read,Adc_ReadGroup" --out engineering/traceability/source_hits.json
```

## Validate and create a review report
```bash
python .github/skills/autosar-hw-code-traceability/scripts/check_traceability.py examples/traceability.example.json
python .github/skills/autosar-hw-code-traceability/scripts/build_review_report.py examples/traceability.example.json --out engineering/reports/review_report.md
```
The example contains deliberately unknown placeholders. Replace it with evidence-backed records for your project before using the report for engineering decisions.

## Run tests
```bash
python -m unittest discover -s tests -v
```

Replace example paths and identifiers with actual project values. Do not put confidential PDFs or customer source into a public repository. Add generated extraction output to .gitignore according to your data-governance rules.

## Recommended first pilot
Choose one contained function, such as a GPIO indicator or ADC input. Confirm one end-to-end chain from schematic page to chip pin specification, ECUC/ARXML, MCAL/IoHwAb/SWC implementation and a test. Record unknowns instead of guessing.
