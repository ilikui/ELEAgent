# PDF analysis and evidence rules

1. Inventory file name, size, SHA-256, metadata, page count and revision.
2. Extract selectable text per page; keep page boundaries and source references.
3. Flag low-text pages for visual/OCR review. This is a heuristic: vector schematics may also contain little extractable text.
4. Render pages for visual review when needed. OCR output is tentative and must be checked against the page.
5. Verify net labels, cross-sheet references, junction dots, pin numbers, units, decimal points, minus signs and component values visually.
6. For polarity, inspect the whole circuit including transistor stages, optocouplers, pull resistors and device input polarity.
7. For MCU facts, use the exact ordering code/package and correct datasheet/reference manual/errata revision.
8. Every accepted fact stores document ID, revision, page, section/region, extraction method, confidence and reviewer state.
