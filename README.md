# ELEAgent

Evidence-driven engineering assistant for embedded and automotive ECU projects.

## AUTOSAR Hardware-to-Code Traceability

A read-only-first workflow for connecting circuit schematic PDFs and semiconductor documentation with AUTOSAR ARXML, ECUC configuration, MCAL/BSW/IoHwAb/RTE/SWC source code, and verification evidence.

### Quick start

```bash
python -m pip install -r requirements.txt
python .github/skills/autosar-hw-code-traceability/scripts/extract_pdf.py path/to/schematic.pdf --out engineering/extracted/pdf_text --render
python .github/skills/autosar-hw-code-traceability/scripts/analyze_arxml.py path/to/arxml --out engineering/traceability/arxml_analysis.json
python .github/skills/autosar-hw-code-traceability/scripts/scan_source.py . --terms "CONFIRMED_NET,Dio_WriteChannel,Rte_Read"
python -m unittest discover -s tests -v
```

See [getting started](docs/getting-started.md), [architecture](docs/architecture.md), [data model](docs/data-model.md), [Phase 2 notes](docs/phase-2.md), and the [Copilot Skill](.github/skills/autosar-hw-code-traceability/SKILL.md).

### Safety model

- Analyze and report by default; do not edit project files until the user approves a concrete change plan.
- Never invent pins, electrical polarity, register values, requirements, tool results, or build outcomes.
- Preserve document revisions, PDF pages, ARXML paths/references, source locations, and verification logs.
- Treat generated code through its authoritative configuration/generator workflow.
- Host tests and static checks do not prove ECU electrical correctness or functional-safety compliance.
- Do not commit customer PDFs, chip manuals under restricted licenses, proprietary source or generated confidential artifacts to a public repository.
