---
name: circuit-schematic-analysis
description: Evidence-backed analysis of electronic circuit schematics, including component identification, pin and net tracing, cross-sheet connections, automotive ECU power/reset/clock, CAN/LIN, sensor, actuator, protection and MCU interface circuits. Use with PDF/image-capable tools and hand off hardware-to-software mappings to autosar-hw-code-traceability.
---

# Circuit Schematic Analysis

## Purpose and boundary

Analyze circuit schematics as engineering evidence, not as a substitute for electrical design review, simulation, bench measurement or OEM approval. Default to read-only analysis. Never modify project files or claim a circuit is correct unless the evidence and applicable requirements support that conclusion.

This is an Agent Skill, not an MCP server. Use only file, image, PDF, search and execution tools actually exposed by the current client. The ELEAgent MCP `extract_pdf` tool extracts selectable text and can render pages; it does **not** perform OCR, symbol recognition, electrical-net reconstruction or circuit simulation. If page images cannot be viewed, report the schematic analysis as incomplete and request a supported image/PDF workflow rather than guessing.

## Required inputs and baseline

1. Establish the project root, branch/commit/status and preserve existing changes.
2. Inventory schematic PDFs/images, native CAD/netlist exports if available, connector tables, BOM, chip datasheets/reference manuals/errata, requirements, ARXML/ECUC, source code and verification artifacts.
3. Record each document's filename, controlled revision/date if explicitly present, page count, SHA-256 where available, and source of the revision. PDF metadata alone is not proof of document revision.
4. Prefer native CAD/netlist exports for exact connectivity when available; use rendered PDFs for visual review. Treat OCR and visual transcription as tentative until checked against the drawing.
5. Ask for missing design context only when it changes the interpretation; record unresolved assumptions explicitly.

## Analysis workflow

### 1. Page and drawing orientation

- Determine title block, sheet number/title, project/ECU variant, revision, units, symbols/legends and drawing conventions.
- Inspect all relevant pages at sufficient resolution. For dense pages, zoom/crop relevant regions without losing page and coordinate context.
- Separate selectable text, OCR-derived text, visually read labels and values from authoritative netlist/CAD data.
- Build a page index and mark pages requiring human visual review.

### 2. Component inventory

Capture, where legible:
- Reference designator (e.g. Uxx, Qxx, Rxx, Cxx, Dxx, Fxx, Lxx, Jxx), symbol/part number, value, package and fitted/DNP status.
- Pin numbers and pin names; pin electrical type when specified by the authoritative component datasheet.
- Component purpose as a **hypothesis** until supported by topology, part documentation and requirements.
- Evidence: schematic document/revision/page, reference designator and a short supporting observation.
- Confidence: `high` only when directly legible and corroborated; `medium` for a legible but uncorroborated interpretation; `low` for ambiguous/OCR-only evidence. Use `unknown` for unreadable or absent information.

Do not infer a part number from a symbol shape or typical circuit alone. Do not infer an unpopulated component is fitted.

### 3. Pin and net connectivity

- Record each observed component-pin-to-net relationship as an individual evidence-backed edge.
- Distinguish a visible wire/junction, a named net connection, a bus, a connector pin, a power symbol, a ground symbol and mere visual proximity.
- A crossing is not a connection unless the drawing's junction convention or authoritative netlist confirms it.
- Normalize label spelling only in a separate field; preserve the exact source spelling as drawn.
- Record signal direction, polarity and electrical domain only when supported by symbol conventions, chip documentation or requirements.
- For each MCU/SoC pin, capture exact device ordering code, package, pin number/name, mux/peripheral function and datasheet revision/page/table where available.
- Do not conclude that two same-named labels connect across pages until label scope, hierarchy, sheet references and CAD/netlist conventions have been checked.

### 4. Cross-sheet and off-page connections

For each off-page connector or continuation:
1. Record source sheet/page, exact label, arrow/port type and destination reference as printed.
2. Find the candidate destination sheet and confirm the exact label, direction and hierarchy.
3. Verify with native netlist/CAD export where possible.
4. Record the link as `confirmed`, `candidate`, `ambiguous` or `not found`; include the reason and evidence on both ends.
5. Do not silently bridge different labels, inferred aliases, similarly named nets or visually similar symbols.
6. Keep a list of unresolved dangling references and contradictory labels for human review.

### 5. Automotive ECU circuit checklist

Only analyze circuit families actually present in the design.

- **Power entry and rails:** battery input, reverse-polarity protection, fuse, TVS, EMI filter, buck/LDO stages, enable pins, power-good, rail sequencing, decoupling and ground returns. Compare ratings and operating range with requirements and datasheets; do not infer automotive transient compliance from the presence of a TVS.
- **MCU reset, boot and clock:** reset supervisor, pull resistors, boot straps, oscillator/crystal network, load capacitors and clock-source constraints. Confirm exact MCU/package and startup requirements.
- **CAN/CAN FD:** transceiver part and supply, MCU TXD/RXD/standby pins, CANH/CANL routing, termination/split termination, common-mode/bus protection and connector path. Do not assume a 120-ohm termination is required at every ECU; verify topology and network architecture.
- **LIN:** transceiver, LIN bus pin, master pull-up/diode arrangement where applicable, wake/sleep and MCU control signals. Validate against the selected transceiver datasheet and network requirements.
- **Sensors and ADC:** sensor supply/return, signal conditioning, divider, RC filter, clamps, reference, ADC mux/channel and scaling. Record component tolerances and error budget only when values/specifications are available.
- **Actuators and drivers:** high-side/low-side drivers, MOSFET/BJT, gate/base networks, flyback/freewheel paths, current sense, diagnostics and safe state. Treat inductive energy and fault behavior as safety-relevant.
- **Digital I/O and communication:** pull-up/down, level shifting, open-drain/push-pull, isolation, series resistance, ESD protection and pin voltage compatibility.
- **Safety and diagnostics:** watchdog, voltage monitoring, redundant paths, plausibility inputs and fault reporting. Do not claim functional-safety compliance from schematic inspection alone.
- **Grounding and EMC:** return paths, chassis/signal ground distinction, shield termination, filter placement and layout-dependent behavior. A schematic alone cannot prove PCB layout or EMC performance.

### 6. Cross-check datasheets and requirements

For every consequential component/pin:
- Match exact manufacturer and full ordering code, package, voltage grade and temperature grade.
- Cite document revision, section/table/figure/page and the relevant requirement.
- Check pin mux and absolute-maximum/operating limits separately; absolute maximum is not a normal operating target.
- Separate design intent, datasheet constraint, requirement, schematic observation and measured behavior.
- Mark missing tolerance, derating, transient, EMC or thermal evidence as a review gap rather than a confirmed defect.

### 7. Findings and severity

Classify each item as:
- `confirmed_issue`: contradictory evidence or a verified violation of an explicit requirement/specification;
- `potential_issue`: plausible concern requiring additional evidence or engineering calculation;
- `requirement_gap`: requirement or acceptance criterion missing/ambiguous;
- `evidence_gap`: a connection, component, pin, revision or source cannot be verified;
- `verification_gap`: required simulation, measurement, bench, HIL or vehicle evidence is absent.

Each finding must contain stable ID, severity, confidence, affected component/net/pin/sheet, expected condition and its source, observed evidence, impact, assumptions, next verification step and open questions. Never label a potential issue as a confirmed defect because a common circuit pattern looks unusual.

## Suggested deliverables

Create or present these artifacts without overwriting existing files unless the user approves:
- `schematic_inventory.md`: documents, revisions, sheet index and limitations.
- `hardware_inventory.json`: components, pins, nets, cross-sheet links, evidence and confidence.
- `circuit_findings.md` or JSON: review findings and unresolved questions.
- `hardware_to_software_traceability.json`: selected signal paths into MCU/ECUC/ARXML/source.
- `verification_plan.md`: calculations, datasheet checks, ERC/netlist checks, simulation and physical measurements still needed.

Use `examples/hardware_inventory.example.json` as a schema illustration only. Never copy example component names, nets, values or pin mappings into a customer project.

## Export PIN and signal inventory to Excel

When the user requests an Excel PIN/signal list, first build or review `hardware_inventory.json` using the field conventions in `examples/hardware_inventory.example.json`. Do not export directly from unverified visual guesses. Each pin row should include, where available:

- Signal/net name exactly as drawn and normalized name as a separate field.
- Device class: `MCU`, `扩展芯片`, `收发器`, `驱动芯片`, `电源芯片`, `连接器`, `其他IC`, `分立器件` or `未确认`.
- Device reference designator, exact part number, package, pin number/name and datasheet pin function/mux function.
- Explicit function-owner classification indicating whether the function belongs to the MCU, an I/O expander, or another device. Do not infer this solely from a signal name.
- Connected net/endpoints, direction, electrical domain, schematic page/sheet, datasheet revision/page/table, evidence, confidence and review state.

The Excel workbook must contain at least:
1. `PIN信号清单`: one row per pin record, with device class and function owner clearly visible.
2. `器件清单`: one row per component/device.
3. `网络与跨页`: net endpoints and cross-sheet link status.
4. `字段说明`: interpretation and limitations.

Use the maintained exporter from the ELEAgent repository (requires `openpyxl`):

```bash
python .github/skills/autosar-hw-code-traceability/scripts/export_pin_excel.py engineering/traceability/hardware_inventory.json --out engineering/reports/pin_signal_inventory.xlsx
```

In VS Code + Copilot, the `export_pin_excel` MCP tool can invoke the same exporter if listed and available. Exporting formats existing JSON evidence; it does not discover missing pins or prove electrical connectivity. Unknown device classes must remain `未确认`, not be guessed. Keep customer-specific output out of public commits.

## Integration with AUTOSAR Hardware-to-Code Traceability

Use this Skill first for physical connectivity and circuit context. Then hand off confirmed hardware evidence to `autosar-hw-code-traceability` for software/configuration traceability:

`requirement -> schematic sheet/component/net/connector/MCU pin -> datasheet pin/peripheral -> ECUC/ARXML -> MCAL/BSW/IoHwAb -> RTE/SWC -> test/measurement`

- Pass exact source references and confidence with every handoff; do not pass a guess as a confirmed fact.
- Search source code only using labels, pin names, peripheral instances or APIs supported by evidence. Text search hits are discovery hints, not proof of runtime data flow.
- If the software/configuration uses an alias different from the schematic label, record the explicit mapping evidence or leave the edge unresolved.
- Keep physical-net evidence distinct from software-signal names and ARXML references.
- Use the existing traceability checker/report generator only for its documented structure/reporting functions; do not imply it validates electrical connectivity or AUTOSAR semantics.
- Any proposed circuit, ARXML or source change requires a separate change plan and explicit approval.

## Final review checklist

- [ ] Every claimed connection has a page/netlist reference and confidence.
- [ ] Cross-sheet links have both endpoints or are explicitly unresolved.
- [ ] Exact MCU/IC part and package were checked against authoritative documentation.
- [ ] Electrical domains, polarity and direction are evidenced rather than guessed.
- [ ] Requirements, tolerances and applicable operating conditions are cited.
- [ ] Visual/OCR ambiguities and unreadable labels are listed.
- [ ] Schematic findings are kept separate from software trace findings.
- [ ] Simulation/bench/CANoe/HIL/vehicle tests are marked NOT RUN unless actually performed.
- [ ] No project files were changed without explicit approval.
