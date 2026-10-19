# ELEAgent repository instructions

For hardware schematic + semiconductor documentation + AUTOSAR analysis, follow .github/skills/autosar-hw-code-traceability/SKILL.md.

For PDF books, chip manuals, AUTOSAR specifications and document collections that should become reusable study/reference material, follow .github/skills/pdf-book-to-skill/SKILL.md and docs/pdf-book-to-skill.md.

- Default to read-only analysis. Do not modify source, ARXML, ECUC configuration, generated files or build scripts until the user approves a specific change plan.
- Never invent hardware facts, register addresses, AUTOSAR APIs, requirements, build commands or test results.
- Cite schematic PDF revision/page/net/component/pin, chip manual revision/section/page, ARXML path/XPath, and source path/symbol/line range.
- Distinguish text-search hits from verified call/data-flow relationships.
- Identify generated code and the authoritative generator/configuration before proposing modifications.
- Preserve user changes; propose minimal diffs; state exactly what was and was not verified.
- Keep proprietary PDFs, customer schematics and generated book-derived knowledge skills out of public commits unless redistribution is explicitly authorized.
