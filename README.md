# ELEAgent

Evidence-driven engineering assistant for embedded and automotive ECU projects.

ELEAgent combines **Agent Skills** (workflow and domain instructions) with local Python tooling for PDF extraction, ARXML indexing, source discovery and traceability reporting.

> **Important distinction:** a `SKILL.md` is not itself an MCP server. A skill tells an agent *how to reason and which workflow to follow*; an MCP server exposes callable tools. You can use the skill directly in VS Code GitHub Copilot, or pair it with an MCP server that exposes the tools/data you want the agent to access. See [MCP setup](docs/mcp-setup.md).

## Capabilities

- Trace evidence from schematic PDF and semiconductor documentation to MCU pins, ECUC/ARXML, MCAL/BSW/IoHwAb, RTE/SWC and verification.
- Extract selectable PDF text and render pages for visual review.
- Inventory ARXML and heuristically identify cross-file references.
- Search source/configuration for candidate symbols and build evidence-backed review reports.
- Turn user-owned technical PDFs, chip manuals and specifications into private, chapter-based knowledge skills using the [PDF-to-Skill workflow](.github/skills/pdf-book-to-skill/SKILL.md), adapted from [book-to-skill](https://github.com/virgiliojr94/book-to-skill).

## Use as a VS Code GitHub Copilot Skill

Open this repository in VS Code with GitHub Copilot enabled. Project skills live in `.github/skills/*/SKILL.md` and are discovered by supported Copilot agent experiences.

Available skills:

| Skill | Use it for |
|---|---|
| [autosar-hw-code-traceability](.github/skills/autosar-hw-code-traceability/SKILL.md) | Hardware-to-code traceability, ARXML/config/source analysis and review reports |
| [pdf-book-to-skill](.github/skills/pdf-book-to-skill/SKILL.md) | Convert PDF books/manuals into structured, citation-backed local knowledge |

Example prompts:

- `Use /autosar-hw-code-traceability to trace this schematic signal through ARXML and source. Analyze only; do not edit files.`
- `Use /pdf-book-to-skill to outline this local PDF, preserve page citations, and prepare a private chapter-based knowledge skill.`

If a skill does not appear, verify the directory contains a file named exactly `SKILL.md`, check its YAML frontmatter, and reload/restart the agent session. Skill support depends on the Copilot client and version.

## Use with MCP

MCP configuration does **not** install a skill by itself. For MCP usage, decide which tools should be callable, then configure an actual MCP server that provides them. ELEAgent currently contains Python scripts and skill instructions; it does not yet ship a dedicated ELEAgent MCP server or a ready-to-run `mcp.json`.

Follow [docs/mcp-setup.md](docs/mcp-setup.md) for:
1. choosing the client (VS Code local agent, GitHub Copilot cloud agent/review, or another MCP client);
2. keeping the skill available to the agent;
3. connecting the relevant filesystem/repository MCP tools where supported;
4. the next step if you want the ELEAgent Python scripts exposed as native MCP tools.

Do not point an MCP client at a `SKILL.md` file as though it were a server command or URL. Do not paste a sample configuration until its command/URL matches an installed, reachable MCP server.

## Quick start: local Python tools

Python 3.10+ is recommended.

```bash
python -m pip install -r requirements.txt
python .github/skills/autosar-hw-code-traceability/scripts/extract_pdf.py path/to/schematic.pdf --out engineering/extracted/pdf_text --render
python .github/skills/autosar-hw-code-traceability/scripts/analyze_arxml.py path/to/arxml --out engineering/traceability/arxml_analysis.json
python .github/skills/autosar-hw-code-traceability/scripts/scan_source.py . --terms "CONFIRMED_NET,Dio_WriteChannel,Rte_Read"
python -m unittest discover -s tests -v
```

See [getting started](docs/getting-started.md), [architecture](docs/architecture.md), [data model](docs/data-model.md), [Phase 2 notes](docs/phase-2.md), and the [PDF-to-Skill integration guide](docs/pdf-book-to-skill.md).

## Safety model

- Analyze and report by default; do not edit project files until the user approves a concrete change plan.
- Never invent pins, electrical polarity, register values, requirements, tool results, or build outcomes.
- Preserve document revisions, PDF pages, ARXML paths/references, source locations, and verification logs.
- Treat generated code through its authoritative configuration/generator workflow.
- Host tests and static checks do not prove ECU electrical correctness or functional-safety compliance.
- Do not upload or publicly commit customer PDFs, restricted chip manuals, proprietary source, or confidential book-derived skills without authorization.
