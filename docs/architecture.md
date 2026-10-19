# Architecture and data flow

## Processing pipeline
1. Inventory PDFs, chip documents, ARXML, ECUC, source, generated output, tests and build files; record hashes and revisions.
2. Extract selectable PDF text page-by-page; render low-text or ambiguous pages; keep OCR tentative and reviewable.
3. Curate hardware facts: net/component/pin/topology, schematic page/region and exact chip-document revision/section.
4. Analyze AUTOSAR artifacts with namespace-aware XML parsing; preserve XPath, short names, reference targets and variant context. Use vendor schemas/tools for authoritative validation.
5. Search source/configuration. Add compiler-based indexing/call-graph tools when available; plain text matches remain hints.
6. Link requirements, hardware, chip constraints, ECUC/ARXML, software layers and verification in traceability records.
7. Produce a review report and minimal proposed change plan.
8. Wait for explicit approval before edits.
9. Execute known project checks; distinguish host tests, target builds and hardware validation.

## PDF-to-Skill knowledge workflow
For books and technical documents intended for repeated study, use `.github/skills/pdf-book-to-skill/SKILL.md`. This adapts the book-to-skill pattern by separating local deterministic extraction from chapter-aware knowledge generation, and creates an on-demand skill with chapter files, glossary, patterns and cheatsheet. See [PDF integration](pdf-book-to-skill.md) and the [upstream project](https://github.com/virgiliojr94/book-to-skill).

PDF-derived study notes are not evidence of a project's actual hardware wiring, ARXML configuration or runtime behavior. Keep the document-learning workflow separate from the ECU traceability evidence chain.

## Trust states
- extracted: machine-extracted but not reviewed
- human_reviewed: reviewer checked source page/element
- cross_checked: corroborated by another authoritative source
- unknown: not established

Confidence is not safety approval. A reviewed fact may still be incomplete if the document revision or hardware variant is uncertain.

## Limitations
PDF text extraction cannot reliably infer schematic connectivity, junctions or polarity. XML well-formedness does not establish AUTOSAR schema/semantic correctness. Text search does not establish call graph/data flow. Build scripts may require proprietary toolchains. This toolkit does not certify functional-safety compliance.
