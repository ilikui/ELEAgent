---
name: autosar-hw-code-traceability
description: Evidence-backed analysis of circuit schematic PDFs, semiconductor manuals, AUTOSAR ARXML/configuration, embedded source and verification. Read-only by default; require approval before edits.
---

# AUTOSAR Hardware-to-Code Traceability

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
Extract selectable text page-by-page and preserve page boundaries. Record file hash, metadata, page count and revision if discoverable. Flag low-text pages for OCR/visual review; do not assume every such page is scanned. Inspect page images for symbols, junctions, cross-sheet nets, pin numbers and polarity. OCR is a candidate transcription, never ground truth.
Record the exact chip ordering code/package, document revision, page and section. Cross-check datasheet, reference manual and errata.

### 2. Build hardware inventory
Identify components, MCU pins, net labels, connectors, power/reset/clock circuits, peripheral signals, external drivers, pull resistors, dividers, filters and protection circuits. Trace active polarity through the complete external circuit. Do not infer connectivity from proximity or signal names. Mark unresolved or ambiguous connections as needing human review.

### 3. Analyze AUTOSAR artifacts
Inventory ARXML namespaces/schema versions and configuration variants. Extract relevant SWC ports/interfaces/data elements/runnables/mappings and ECUC module/container/parameter values where present. Trace Com/PduR/CanIf/driver, DIO/ADC/PWM and IoHwAb paths only where project artifacts support them. Record file paths, XPath, short names, references and variant conditions. Text search is discovery, not proof that references resolve or configuration is valid.

### 4. Trace source code
Search maintained source and configuration for net names, pin names, peripheral instances, APIs, RTE symbols, runnable names, callbacks, state transitions and tests. Identify call/data flow where possible. Label simple text hits as hints, not proven relationships. Check initialization order, safe startup state, polarity, data scaling, timeout/fault behavior, task periods, concurrency and error handling against explicit requirements.

### 5. Create traceability records
For each function/signal, connect as much evidence as available:
- requirement and intended behavior
- schematic document/revision/page/component/net/pin
- chip document/revision/section/page/register or pin specification
- ECUC configuration and ARXML element/XPath
- MCAL/BSW/IoHwAb implementation
- RTE/SWC runnable, port and data element
- test, measurement point and acceptance criterion
Every missing link must be explicit.

### 6. Report findings
Each finding includes stable ID, severity, category, confidence, expected behavior and its evidence, actual implementation and location, gap/impact, assumptions, minimal proposed change, verification plan and open questions. If requirements or hardware facts are missing, do not call the behavior a confirmed defect.

### 7. Approval gate
Present a proposed change plan listing exact files, rationale, risk, generated-code implications, tests and rollback considerations. Wait for explicit user approval. Approval to analyze is not approval to edit. After approval, apply only agreed changes, inspect the full diff and preserve unrelated changes.

### 8. Verify
Run only documented or explicitly supplied commands. Record exact command, working directory, exit code, toolchain/version and log path. Report tests/builds not run and why. Mark oscilloscope, bench, CANoe, HIL and vehicle checks NOT RUN unless actually performed.

## Deliverables
- inventory.md: input documents, revisions, source/build inventory and limitations
- hardware inventory YAML/JSON with evidence and review state
- traceability.json and CSV
- findings.json and review_report.md
- verification_report.md with actual commands and results
- patch only after approval

## Completion criteria
All findings are evidence-backed or explicitly marked uncertain; unknowns and tool limitations remain visible; the change plan is reviewable; no unapproved project files were modified.
