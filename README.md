# ELEAgent

Evidence-driven engineering assistant for embedded and automotive ECU projects.

ELEAgent combines reusable Agent Skills with a **local MCP server implementation** and Python tools for chip-manual and schematic PDF indexing, ARXML reference discovery, C/C++ source search, traceability checks and review-report generation.

> A SKILL.md is not an MCP server. The Skill provides the analysis workflow; mcp_server.py exposes callable tools over MCP stdio. Keep both enabled so Copilot has both domain instructions and tools.

## Capabilities

- Analyze chip datasheets/reference manuals by device identity, pinout, mux, electrical limits, registers, timing, reset/clock/boot and errata; keep page-level evidence and review gaps.
- Extract candidate pin, pin-mux, register, electrical-limit and timing tables into JSON while preserving raw cells, PDF page numbers and review flags.
- Normalize recognized table headers into reviewable candidate pin/register/electrical records while retaining raw rows and page provenance.
- Compare label-matched manual identity candidates (part number, package, document revision and silicon revision) with an optional BOM/device manifest; all matches remain unconfirmed.\n- Merge identity review results into matching hardware inventory components without overwriting BOM/source fields, then carry the review status and page evidence into the Excel component sheet.
- Trace evidence from schematic PDFs and chip documentation to MCU pins, ECUC/ARXML, MCAL/BSW/IoHwAb, RTE/SWC and verification.
- Extract selectable PDF text by page, record SHA-256 and flag low-text pages for visual review; optionally render pages.
- Inventory ARXML references heuristically; not a substitute for release-specific XSD/vendor ECUC validation.
- Search C, C++, headers and supported configuration files for user-supplied terms.
- Validate traceability record structure and generate Markdown review reports.
- Export PIN/signal inventories to Excel with MCU vs I/O-expander/device classification, component inventory and cross-sheet net sheets.
- Turn technical PDFs into private, chapter-based knowledge using the PDF-to-Skill workflow.

## VS Code + GitHub Copilot MCP setup

This repository includes .vscode/mcp.json, configured for a local stdio server.

1. Clone and open this repository in VS Code.
2. Install Python 3.10 or newer.
3. Install dependencies with `python -m pip install -r requirements.txt`.
4. Open Copilot Chat in Agent mode and approve the workspace MCP server after reviewing its configuration.
5. Run **MCP: List Servers** and check that eleagent is running.
6. Ask Copilot to use get_workspace_info, then try analyze_chip_manual on a local chip PDF.

If the MCP server does not start, confirm Python is on PATH and inspect the server output/logs.

### Important workspace boundary

The default ELEAGENT_WORKSPACE is the opened workspace folder. Paths passed to tools are relative to that folder. For best results, open the ECU project folder as the workspace and keep the ELEAgent scripts available at the configured server path. Keep private paths and customer-specific configuration out of public commits.

See [MCP setup and security guide](docs/mcp-setup.md).

## Available MCP tools

| Tool | Purpose | Writes |
|---|---|---|
| get_workspace_info | Report configured workspace and available tools | No |
| extract_pdf | Extract selectable per-page text, manifest and optional page images | Extraction output only |
| analyze_chip_manual | Build a topic/page index of a chip manual, including document hash, snippets and review gaps | JSON report only |
| extract_chip_manual_tables | Extract candidate tables with raw cells, PDF page, topic hints and review flags | JSON report only |
| normalize_chip_manual_tables | Map recognized headers into candidate records while preserving raw rows, page citations and review status | JSON report only |
| review_chip_identity | Compare manual identity candidates with an optional BOM/device manifest, preserving page evidence and hashes | JSON report only |\n| merge_chip_identity_review | Attach review evidence to inventory components by reference without overwriting source fields | Merged JSON for downstream Excel export |
| analyze_arxml | Index ARXML elements and candidate references | JSON report only |
| scan_source | Search C/C++ and supported configuration files | JSON report only |
| check_traceability | Validate traceability JSON shape and flag gaps | No |
| build_review_report | Generate a Markdown evidence review | Report only |
| export_pin_excel | Export PIN/signal inventory JSON to a multi-sheet Excel workbook | Workbook only |

All input/output paths are restricted to ELEAGENT_WORKSPACE; absolute paths and path traversal are rejected. No tool is exposed for editing source, ARXML, ECUC configuration or generated code.

## Agent Skills

| Skill | Use it for |
|---|---|
| [chip-datasheet-analysis](.github/skills/chip-datasheet-analysis/SKILL.md) | Evidence-backed reading of chip manuals, pin mux, electrical limits, registers, timing and errata |
| [circuit-schematic-analysis](.github/skills/circuit-schematic-analysis/SKILL.md) | Component, pin, net, cross-sheet and automotive ECU circuit analysis |
| [autosar-hw-code-traceability](.github/skills/autosar-hw-code-traceability/SKILL.md) | Evidence-based hardware-to-code tracing and review |
| [pdf-book-to-skill](.github/skills/pdf-book-to-skill/SKILL.md) | Convert technical PDFs into private, cited knowledge |

## Example prompts

- "Use /chip-datasheet-analysis to analyze this exact MCU manual. Identify the ordering code, package and revision. Index pin mux, electrical limits, registers, timing and errata with PDF page citations. Mark ambiguous tables for visual review."
- "Use /chip-datasheet-analysis on the I/O expander datasheet, then compare its pin functions with the schematic and export the reviewed PIN matrix to Excel."
- "Use /circuit-schematic-analysis first, then /autosar-hw-code-traceability to trace evidenced MCU signals through ARXML and C/C++ source."
- "Use /pdf-book-to-skill to outline this local PDF, preserve page citations and keep generated knowledge private."

## Run locally without MCP

```bash
python -m pip install -r requirements.txt
python .github/skills/autosar-hw-code-traceability/scripts/extract_pdf.py path/to/chip_manual.pdf --out engineering/extracted/pdf_text --render
python .github/skills/autosar-hw-code-traceability/scripts/analyze_chip_manual.py path/to/chip_manual.pdf --out engineering/chip_manual/chip_manual_analysis.json
python .github/skills/autosar-hw-code-traceability/scripts/extract_chip_tables.py path/to/chip_manual.pdf --out engineering/chip_manual/chip_manual_tables.json
python .github/skills/autosar-hw-code-traceability/scripts/normalize_chip_tables.py engineering/chip_manual/chip_manual_tables.json --out engineering/chip_manual/chip_manual_review_records.json
python .github/skills/autosar-hw-code-traceability/scripts/review_chip_identity.py engineering/chip_manual/chip_manual_analysis.json --out engineering/chip_manual/chip_identity_review.json\npython .github/skills/autosar-hw-code-traceability/scripts/merge_chip_identity.py engineering/hardware/hardware_inventory.json engineering/chip_manual/chip_identity_review.json --out engineering/chip_manual/hardware_inventory_with_identity.json\npython .github/skills/autosar-hw-code-traceability/scripts/export_pin_excel.py engineering/chip_manual/hardware_inventory_with_identity.json --out engineering/reports/pin_signal_inventory.xlsx
# Optional: add --manifest path/to/your_device_manifest.json when you have a BOM manifest
python .github/skills/autosar-hw-code-traceability/scripts/analyze_arxml.py path/to/arxml --out engineering/traceability/arxml_analysis.json
python .github/skills/autosar-hw-code-traceability/scripts/scan_source.py . --terms "CONFIRMED_NET,Dio_WriteChannel,Rte_Read"
python .github/skills/autosar-hw-code-traceability/scripts/export_pin_excel.py .github/skills/circuit-schematic-analysis/examples/hardware_inventory.example.json --out /tmp/pin_signal_inventory.xlsx
python -m unittest discover -s tests -v
```

## Safety and evidence rules

- Analyze and report by default; no project-file modification tools are exposed.
- Never invent pin numbers, electrical polarity, register values, requirements, tool results or build outcomes.
- Preserve document revisions, PDF pages, ARXML paths/references, source locations and verification logs.
- Treat generated code through its authoritative configuration/generator workflow.
- Host tests and static checks do not prove ECU electrical correctness or functional-safety compliance.
- Do not transmit or publicly commit customer PDFs, restricted chip manuals, proprietary source or confidential book-derived knowledge without authorization.
