---
name: chip-datasheet-analysis
description: Evidence-backed interpretation of semiconductor datasheets and reference manuals, including pinouts, multiplexed functions, electrical limits, timing, registers, peripherals, package variants, errata and design constraints.
---

# Chip Datasheet Analysis

## Mission

Read semiconductor datasheets, reference manuals, programming manuals and errata as controlled engineering evidence. Convert document content into a cited engineering explanation and structured records that can feed schematic analysis, PIN Excel export and AUTOSAR hardware-to-code traceability.

This Skill does not make a language model or PDF text extractor a substitute for the original manual. Never claim a limit, register address, bit field, pin mux, reset value, package pin number or timing value without a source citation.

## Identify the exact device first

Capture manufacturer, full part/order code, silicon family/revision, package and pin count, voltage/temperature grade, document title/number/revision/date, applicable device variants, errata, PDF filename, SHA-256 and page count. A family-level manual may cover several derivatives. Keep device/variant applicability for every extracted fact. If exact ordering code or package is unknown, explicitly state what cannot safely be concluded.

## Read in layers

1. **Document map:** table of contents, revision history, ordering information, package options and document conventions.
2. **Pinout:** pin assignment tables and package drawings; pin number, name, I/O type, power domain, reset state and package applicability.
3. **Pin multiplexing:** alternate functions, peripheral instance, mux selection, restrictions, analog functions, debug/boot functions and conflicts between functions sharing a pad.
4. **Electrical characteristics:** recommended operating conditions, absolute maximum ratings, input thresholds, output drive/VOH/VOL, leakage, injection current, ADC characteristics, oscillator limits and temperature conditions.
5. **Power/reset/clock/boot:** supply domains, ramp and sequencing requirements, decoupling recommendations, reset timing, boot straps and clock startup constraints.
6. **Peripheral architecture:** GPIO, ADC, timers/PWM, DMA, SPI, I2C, UART, CAN/LIN/Ethernet, watchdog, safety/security and memory interfaces as relevant.
7. **Registers:** address/offset, access width, reset value, bit positions, field meaning, access type (RO/RW/W1C etc.), reserved-bit rules, clock/power prerequisites and write sequence.
8. **Timing and operating constraints:** setup/hold, bus timing, sampling rate, conversion timing, clock limits, latency, startup/shutdown, interrupt/DMA interactions and errata workarounds.
9. **Cross-checks:** reconcile datasheet, reference manual, package document, errata, schematic and requirements. Record conflicts instead of silently selecting one.

## Evidence and citations

Every engineering claim affecting implementation or electrical correctness must include document ID/revision/date, exact PDF page (1-based), section/table/figure/register name when detectable, a short evidence excerpt or transcription, extraction method, confidence, device/package applicability, review status and conditions/units/min/typ/max/footnotes.

Distinguish PDF viewer page numbers from printed page labels. Preserve physical PDF page index as the stable citation and store printed page label separately when available.

## Engineering interpretation rules

- Keep absolute maximum ratings separate from recommended operating conditions and normal functional specifications. Absolute maximum ratings are not design targets.
- Preserve min/typ/max and the conditions attached to every electrical value.
- Treat pin mux as package- and derivative-specific. A peripheral existing in the family does not prove it is available on a particular pin/package.
- Treat register addresses as base address + offset only when both are sourced and the applicable memory map is clear. Preserve access semantics and reserved bits.
- Include documented reset, clock enable, peripheral reset, security state and power-domain prerequisites that affect register behavior.
- Do not infer board connectivity from pin function tables; schematic/netlist evidence proves board connections.
- Do not infer source-code runtime behavior from a register description alone.
- If PDF text is garbled, scanned, table columns are interleaved, or footnotes cannot be associated with values, mark extraction uncertain and inspect a rendered page using an image-capable tool. Never fabricate OCR or visual inspection.
- Search and cite errata before declaring a behavior unsupported or a design defect.
- Treat tables as structured data only when row/column alignment is reliable; otherwise keep the page reference and mark for manual review.

## Outputs

Depending on the request, produce a concise answer with source citations, chip_manual_analysis.json (document metadata, page index, topic hits, evidence snippets and review gaps), pin_function_matrix.json/Excel, register_reference.json, electrical_limits.json, or manual_review_checklist.md.

Use the MCP tool analyze_chip_manual or its CLI helper to build a searchable page/topic index. Use extract_chip_manual_tables to extract candidate tables into raw rows with PDF page citations and topic hints. Treat detected tables as unreviewed candidates: table detection is heuristic, scanned-page OCR is not performed, and merged cells, footnotes and column alignment must be checked against the original rendered page. Neither tool is an autonomous design approval.

## Integration with other Skills

1. Run this Skill on the exact MCU or external-chip manual.
2. Pass sourced pin/device evidence into circuit-schematic-analysis; combine it with schematic/netlist evidence to determine board-level connections.
3. Export reviewed inventory using export_pin_excel. Keep unknown functions/owners explicit.
4. Use autosar-hw-code-traceability to trace evidenced MCU peripheral/pin to ECUC/ARXML, MCAL/BSW/IoHwAb, RTE/SWC and source.
5. Maintain separate evidence edges for manual fact, schematic connection, software mapping and test/measurement.

## Suggested prompt

"Use /chip-datasheet-analysis to read this exact chip manual. First identify device/package/document revision. Build a page-cited index of pin functions, mux restrictions, electrical limits, register maps, reset/clock/boot requirements and errata. Preserve min/typ/max and conditions. Mark scanned or ambiguous tables for visual review. Do not guess; then link confirmed pin facts to the schematic and export a reviewed PIN matrix to Excel."
