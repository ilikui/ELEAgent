---
name: autosar-hw-code-traceability
description: Evidence-backed analysis of circuit schematic PDFs, semiconductor manuals, AUTOSAR ARXML/configuration, embedded source and verification. Use with available workspace or MCP tools; read-only by default and require approval before edits.
---

# AUTOSAR Hardware-to-Code Traceability

## Agent and MCP integration boundary

This file is an Agent Skill: it provides workflow instructions. It is **not** an MCP server and must not be configured as an MCP executable or endpoint. In VS Code, load it through the repository's `.github/skills/` discovery path. When MCP servers are configured, use only tools actually exposed by those servers.

- First inspect the tools available in the current client and determine which can read the workspace, list files, search code, or access GitHub.
- If filesystem/repository tools are unavailable, ask the user to open the repository in a supported local agent or configure an appropriate MCP server; do not pretend to have read local files.
- Prefer read-only file, search and analysis tools. Never assume a tool can run local Python scripts unless it explicitly supports command execution.
- If a required script cannot be executed, provide the exact command for the user to run and clearly mark the analysis as incomplete.
- Do not assume that an MCP server has access to local PDFs just because a file path was mentioned. Confirm the tool's workspace boundary and permissions first.

## Circuit schematic analysis handoff

For physical circuit interpretation, use the independent [circuit-schematic-analysis Skill](../circuit-schematic-analysis/SKILL.md) first when schematic PDFs/images, connector tables, BOMs or native netlists are present. This Skill owns component/pin/net/cross-sheet evidence. Do not treat extracted PDF text alone as a connectivity graph.

Handoff contract:
- Carry forward only observed or source-corroborated component, net and MCU-pin facts.
- Preserve document revision, page/sheet, component reference, pin number, exact net label, evidence and confidence.
- Mark visual guesses and OCR-only readings as candidates; unresolved cross-sheet links remain unresolved.
- Then continue this Skill's hardware-to-code chain from confirmed MCU pin/peripheral into ECUC/ARXML, MCAL/BSW/IoHwAb, RTE/SWC and verification.
- Keep physical connectivity, software naming and ARXML reference matching as separate evidence edges.
- If no image viewer/native netlist is available, report schematic connectivity analysis as incomplete and request a suitable export rather than infer connections.

Recommended prompt: "Use circuit-schematic-analysis to inventory the schematic and resolve page/net/pin evidence first. Then use autosar-hw-code-traceability to trace only supported signals into ARXML and C/C++ code. Report unknowns and do not edit files."

## Mission
Build an evidence-backed chain:
requirement -> schematic component/net/pin -> MCU peripheral -> ECUC/ARXML configuration -> MCAL/BSW/IoHwAb -> RTE/SWC -> observable behavior -> verification.

## Non-negotiable rules
- Default mode is ANALYSIS ONLY. Never modify, generate, format, delete or overwrite project files until the user approves a concrete change plan.
- Never invent pin numbers, net names, active levels, register values, APIs, scaling, thresholds, requirements, file paths or test results.
- Unknown facts are UNKNOWN and require review. A variable name is not proof of a hardware connection.
- Every important conclusion must cite evidence: document/revision/page/section; ARXML file and XPath/element; source path/symbol/line range; actual test command and result.
- Distinguish confirmed defect, potential defect, requirement gap, evidence gap and verification gap.
- Inspect repository status and preserve existing user changes.
- Identify generated code and its authoritative configuration/generator before proposing changes. Do not hand-edit generated artifacts by default.
- Treat safety mechanisms, watchdogs, diagnostic thresholds, fault reactions, memory protection and limp-home behavior as safety-relevant and require human review.
- Do not upload proprietary documents or customer source to external services without authorization.
- A successful host test is not proof of ECU electrical correctness, vehicle behavior or functional-safety compliance.

## Workflow

### 0. Establish baseline
Inventory the project root, Git branch/commit/status, documents, source, ARXML, configuration, generated output, build instructions and tests. Record toolchain versions and baseline results where available. Do not clean or reset the worktree.

### 1. Parse PDF documents
Run extract_pdf.py on each relevant PDF. Preserve page boundaries, SHA-256, metadata and page count. Low-text pages are review candidates, not automatically scanned pages. Inspect page images for symbols, junctions, cross-sheet nets, pin numbers and polarity. OCR is tentative transcription, never ground truth.
Record exact chip ordering code/package, document revision, page and section. Cross-check datasheet, reference manual and errata.

### 2. Build hardware inventory
Identify components, MCU pins, net labels, connectors, power/reset/clock circuits, peripheral signals, external drivers, pull resistors, dividers, filters and protection circuits. Trace active polarity through the complete external circuit. Do not infer connectivity from proximity or signal names. Mark unresolved or ambiguous connections as needing human review.

### 3. Analyze AUTOSAR artifacts
Run inventory_arxml.py for a quick element inventory and analyze_arxml.py for candidate cross-file references. The latter indexes SHORT-NAME paths and reference text; its resolution status is heuristic and not proof of AUTOSAR validity. Record ARXML file, namespace, source element and reference. Validate against the correct release XSD and the vendor configurator/validator when available. Do not treat XML well-formedness or heuristic reference matching as ECUC semantic validation.
Trace SWC ports/interfaces/data elements/runnables/mappings and ECUC module/container/parameter values only when the artifacts support it. Trace Com/PduR/CanIf/driver, DIO/ADC/PWM and IoHwAb paths only when evidenced.

### 4. Trace source code
Run scan_source.py with terms taken from confirmed hardware/configuration evidence. Text matches are discovery hints only. Inspect callers/callees, data flow, initialization, generated-code markers and tests manually or with project-aware tooling. Check startup state, polarity, scaling, timeout/fault behavior, task periods, concurrency and error handling against explicit requirements.

### 5. Create traceability records
For each function/signal, connect as much evidence as available:
- requirement and intended behavior
- schematic document/revision/page/component/net/pin
- chip document/revision/section/page/register or pin specification
- ECUC configuration and ARXML element/XPath
- MCAL/BSW/IoHwAb implementation
- RTE/SWC runnable, port and data element
- test, measurement point and acceptance criterion
Every missing link must be explicit. Use examples/traceability.example.json as a shape example only; never copy example facts into a real project.

### 6. Report findings
Use check_traceability.py to check record shape and build_review_report.py to render a human-review report. These scripts do not establish truth. Each finding includes stable ID, severity, category, confidence, expected behavior and evidence, actual implementation and location, gap/impact, assumptions, minimal proposed change, verification plan and open questions. If requirements or hardware facts are missing, do not call behavior a confirmed defect.

### 7. Approval gate
Present a proposed change plan listing exact files, rationale, risk, generated-code implications, tests and rollback considerations. Wait for explicit user approval. Approval to analyze is not approval to edit. After approval, apply only agreed changes, inspect the full diff and preserve unrelated changes.

### 8. Verify
Run only documented or explicitly supplied commands. Record exact command, working directory, exit code, toolchain/version and log path. Report tests/builds not run and why. Mark oscilloscope, bench, CANoe, HIL and vehicle checks NOT RUN unless actually performed.

## Tool commands
Use these commands only in a local environment where Python and the repository are available. An MCP tool does not automatically have shell access.

```bash
python .github/skills/autosar-hw-code-traceability/scripts/extract_pdf.py path/to/schematic.pdf --out engineering/extracted/pdf_text --render
python .github/skills/autosar-hw-code-traceability/scripts/inventory_arxml.py path/to/arxml --out engineering/traceability/arxml_inventory.json
python .github/skills/autosar-hw-code-traceability/scripts/analyze_arxml.py path/to/arxml --out engineering/traceability/arxml_analysis.json
python .github/skills/autosar-hw-code-traceability/scripts/scan_source.py . --terms "CONFIRMED_NET,Dio_WriteChannel,Rte_Read" --out engineering/traceability/source_hits.json
python .github/skills/autosar-hw-code-traceability/scripts/check_traceability.py examples/traceability.example.json
python .github/skills/autosar-hw-code-traceability/scripts/build_review_report.py examples/traceability.example.json --out engineering/reports/review_report.md
python -m unittest discover -s tests -v
```

## Deliverables
- inventory.md: input documents, revisions, source/build inventory and limitations
- hardware inventory YAML/JSON with evidence and review state
- traceability.json and CSV
- findings.json and review_report.md
- verification_report.md with actual commands and results
- patch only after approval

## Completion criteria
All findings are evidence-backed or explicitly marked uncertain; unknowns and tool limitations remain visible; the change plan is reviewable; no unapproved project files were modified.
