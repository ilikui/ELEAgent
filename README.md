# ELEAgent

Evidence-driven engineering assistant for embedded and automotive ECU projects.

ELEAgent combines reusable Agent Skills with a **local MCP server implementation** and Python tools for PDF extraction, ARXML reference discovery, C/C++ source search, traceability checks and review-report generation.

> A `SKILL.md` is not an MCP server. The Skill provides the analysis workflow; `mcp_server.py` exposes callable tools over MCP stdio. Keep both enabled so Copilot has both domain instructions and tools.

## Capabilities

- Trace evidence from schematic PDFs and chip documentation to MCU pins, ECUC/ARXML, MCAL/BSW/IoHwAb, RTE/SWC and verification.
- Extract selectable PDF text by page, record SHA-256 and flag low-text pages for visual review; optionally render pages.
- Inventory ARXML references heuristically; not a substitute for release-specific XSD/vendor ECUC validation.
- Search C, C++, headers and supported configuration files for user-supplied terms.
- Validate traceability record structure and generate Markdown review reports.
- Turn technical PDFs into private, chapter-based knowledge using the [PDF-to-Skill workflow](.github/skills/pdf-book-to-skill/SKILL.md).

## VS Code + GitHub Copilot MCP setup

This repository includes `.vscode/mcp.json`, configured for a local stdio server.

1. Clone and open this repository in VS Code.
2. Install Python 3.10 or newer.
3. In the repository terminal, install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

4. Open Copilot Chat in **Agent** mode. When VS Code asks whether to trust/start the workspace MCP server, inspect the configuration and approve it if appropriate.
5. Run **MCP: List Servers** from the Command Palette and check that `eleagent` is running. If needed, inspect its output/logs and restart it.
6. Ask Copilot to use `get_workspace_info`, then try `scan_source` or `analyze_arxml` against a small test project.

If the MCP server does not start, confirm `python` is on PATH, run `python -m pip install -r requirements.txt` again, and use **MCP: List Servers → Show Output** to inspect the startup error.

### Important workspace boundary

The default `ELEAGENT_WORKSPACE` is `${workspaceFolder}` in the included configuration. That means paths passed to tools are relative to the folder opened in VS Code. For best results, open the ECU project folder as the workspace and keep the ELEAgent scripts available at the configured server path. If you open ELEAgent itself, the tools will operate on the ELEAgent repository, not a separate ECU repository.

To use the server with a different workspace, adjust the local MCP server configuration so that `ELEAGENT_WORKSPACE` points to the intended project root and the `mcp_server.py` argument points to your local ELEAgent clone. Keep private paths and customer-specific configuration out of public commits.

See the detailed [MCP setup and security guide](docs/mcp-setup.md).

## Available MCP tools

| Tool | Purpose | Writes |
|---|---|---|
| `get_workspace_info` | Report configured workspace and available tools | No |
| `extract_pdf` | Extract per-page text, manifest and optional page images | Extraction output only |
| `analyze_arxml` | Index ARXML elements and candidate references | JSON report only |
| `scan_source` | Search C/C++ and supported configuration files | JSON report only |
| `check_traceability` | Validate traceability JSON shape and flag gaps | No |
| `build_review_report` | Generate a Markdown evidence review | Report only |

All input/output paths are restricted to `ELEAGENT_WORKSPACE`; absolute paths and path traversal are rejected. No tool is exposed for editing source, ARXML, ECUC configuration or generated code. Extraction/report tools can create output files inside the workspace.

## Agent Skills

| Skill | Use it for |
|---|---|
| [autosar-hw-code-traceability](.github/skills/autosar-hw-code-traceability/SKILL.md) | Evidence-based hardware-to-code tracing and review |
| [pdf-book-to-skill](.github/skills/pdf-book-to-skill/SKILL.md) | Convert technical PDFs into private, cited knowledge |

Example prompts:

- `Use /autosar-hw-code-traceability to analyze the opened ECU project. Use the MCP tools where available. Report evidence and unknowns; do not edit files.`
- `Use /pdf-book-to-skill to outline this local PDF, preserve page citations and keep generated knowledge private.`

## Run locally without MCP

```bash
python -m pip install -r requirements.txt
python .github/skills/autosar-hw-code-traceability/scripts/extract_pdf.py path/to/schematic.pdf --out engineering/extracted/pdf_text --render
python .github/skills/autosar-hw-code-traceability/scripts/analyze_arxml.py path/to/arxml --out engineering/traceability/arxml_analysis.json
python .github/skills/autosar-hw-code-traceability/scripts/scan_source.py . --terms "CONFIRMED_NET,Dio_WriteChannel,Rte_Read"
python -m unittest discover -s tests -v
```

## Safety and evidence rules

- Analyze and report by default; no project-file modification tools are exposed.
- Never invent pin numbers, electrical polarity, register values, requirements, tool results or build outcomes.
- Preserve document revisions, PDF pages, ARXML paths/references, source locations and verification logs.
- Treat generated code through its authoritative configuration/generator workflow.
- Host tests and static checks do not prove ECU electrical correctness or functional-safety compliance.
- Do not transmit or publicly commit customer PDFs, restricted chip manuals, proprietary source or confidential book-derived knowledge without authorization.
