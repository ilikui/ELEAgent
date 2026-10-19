---
name: pdf-book-to-skill
description: Turn technical PDF books, chip manuals, AUTOSAR specifications and engineering document sets into a structured, on-demand local knowledge skill. Use when a user wants to read, study, search, or reuse a PDF's methods and chapters from VS Code GitHub Copilot.
---

# PDF-to-Skill for ELEAgent

This skill adapts the workflow ideas from [virgiliojr94/book-to-skill](https://github.com/virgiliojr94/book-to-skill) to the ELEAgent engineering traceability workflow. The upstream project provides its own extractor and agent generator; this repository's integration is a compatible workflow, not a vendored copy of the upstream implementation.

## Outcomes

Convert user-owned PDFs or document sets into a private, searchable skill folder with:
- `SKILL.md`: book purpose, chapter map, concepts, decision rules and links to reference files.
- `chapters/`: one Markdown file per chapter or major section, loaded only when needed.
- `glossary.md`: terms, acronyms and definitions with source page references.
- `patterns.md`: methods, procedures, algorithms, diagnostic flows and anti-patterns.
- `cheatsheet.md`: quick lookups, tables and decision rules.
- `sources.json`: document name, SHA-256, revision/edition if known, page/section citation conventions and extraction notes.

## Safety and source fidelity

- Process source documents locally unless the user explicitly authorizes another processing path.
- Do not commit proprietary chip manuals, customer schematics, confidential standards or generated book-derived skills to a public repository. Default generated output to ignored local folders.
- Do not reproduce a book chapter verbatim. Produce transformative study notes, concise paraphrases and small necessary quotations only.
- Never invent a page, section, equation, pin, register, electrical polarity, AUTOSAR requirement or definition. Use `UNKNOWN` when the PDF does not establish it.
- Preserve citations as `[Document, revision/edition, PDF page N, printed page M if distinguishable, section]`. PDF page and printed page are not always the same.
- Tables, formulas, code listings, schematics, footnotes and scanned pages require visual/manual review. Extracted text alone is not authoritative.
- For chip manuals and AUTOSAR specifications, distinguish normative requirements from examples, notes and recommendations.
- For ELEAgent hardware-to-code work, connect claims to the existing traceability model; never treat a book summary as evidence that the ECU's actual configuration or source matches the book.
- Ask before replacing or folding new sources into an existing skill. Preserve existing chapter notes and report merge conflicts.

## Workflow

### 1. Classify inputs
Inventory PDF(s), editions/revisions, file size, page count, whether text is selectable, language, document type (text-heavy or technical), and intended use (reference or study). Ask one concise question only if intended use changes the depth materially.

### 2. Extract locally
For a quick text-and-page baseline:
```bash
python .github/skills/autosar-hw-code-traceability/scripts/extract_pdf.py path/to/book.pdf --out engineering/extracted/pdf_text --render
```
For the upstream extractor's broader format support and adaptive PDF extraction, install the upstream skill separately (see `docs/pdf-book-to-skill.md`) and follow its current `SKILL.md` and `scripts/extract.py --check` instructions. Prefer its technical extraction mode for books with code, tables and formulas; use text extraction for prose-heavy books. Do not assume a PDF is readable until extraction statistics and sample pages have been checked.

If pages have little or no text, treat them as possible scans. Render and inspect representative pages; use OCR only as a provisional layer, and preserve the original PDF as the authority.

### 3. Analyze before generating
Create a source inventory and chapter outline first. Identify:
- document title, author/organization, edition/revision and publication date if available;
- table of contents and chapter boundaries;
- named frameworks, models, principles, algorithms, workflows and anti-patterns;
- formulas, tables, code examples and terms that need exact verification;
- unclear or missing text and pages requiring human review.

For a large book, work chapter-by-chapter. Do not load the entire extracted book into one prompt when a chapter map and targeted reads can do the job.

### 4. Generate the skill
Build a concise top-level `SKILL.md` that explains when to load each chapter. Put detail in `chapters/` and use stable relative links. Each chapter note should contain:
1. Chapter title and a 3–7 sentence orientation.
2. Core ideas and the author's terminology.
3. Decision rules / procedures / formulas, with assumptions.
4. A worked example or application where supported by the source.
5. Common mistakes and boundary conditions.
6. Source citations with PDF and printed page references where available.
7. Open questions or OCR/table/formula items needing review.

Avoid generic summaries. Extract reusable knowledge and make it easy to retrieve for a concrete question.

### 5. Validate
- Check every generated relative link and ensure all referenced chapter files exist.
- Verify source page citations against the original PDF.
- Compare formulas, table values, register names and code against page images where extraction may have altered layout.
- Check that the glossary and cheatsheet do not assert facts missing from the source.
- Report extraction failures, pages not reviewed and unresolved ambiguities.

### 6. Store privately
Use a local path such as `engineering/library/<skill-slug>/`. Do not commit that folder by default. Publicly share only material the user has the rights to redistribute and has approved for publication.

## Response format

Report:
- source files and revisions;
- extraction method and coverage;
- skill output path;
- chapter count and generated reference files;
- pages needing manual review;
- link/citation validation result;
- privacy/licensing warning where applicable.

Never claim a full book has been verified when only a subset of pages was inspected.
