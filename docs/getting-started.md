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

## Search source and configuration
```bash
python .github/skills/autosar-hw-code-traceability/scripts/scan_source.py . --terms "CONFIRMED_NET_NAME,Dio_WriteChannel,Rte_Read,Adc_ReadGroup" --out engineering/traceability/source_hits.json
```

## Validate reviewed traceability JSON
```bash
python .github/skills/autosar-hw-code-traceability/scripts/check_traceability.py engineering/traceability/traceability.json
```

Replace all example paths and identifiers with actual project values. Do not put confidential PDFs or customer source into a public repository. Add generated extraction output to .gitignore according to your data-governance rules.

## Recommended first pilot
Choose one contained function, such as a GPIO indicator or ADC input. Confirm one end-to-end chain from schematic page to chip pin specification, ECUC/ARXML, MCAL/IoHwAb/SWC implementation and a test. Record unknowns instead of guessing.
