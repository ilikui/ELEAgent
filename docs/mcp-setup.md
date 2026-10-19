# Configure ELEAgent for MCP

This guide distinguishes the reusable ELEAgent **Agent Skills** from **MCP servers**, then explains the supported setup paths.

## 1. Skill versus MCP server

- **Skill**: a `SKILL.md` instruction bundle that teaches a compatible agent when and how to perform a workflow.
- **MCP server**: a running local process or reachable service that exposes callable tools/resources/prompts through the Model Context Protocol.
- **ELEAgent today**: contains Copilot skills and Python command-line scripts. It does **not** currently include a dedicated MCP server executable or a prebuilt MCP endpoint.

Therefore, adding the path to `.github/skills/autosar-hw-code-traceability/SKILL.md` into an MCP server list will not work. Keep the skill loaded by the agent and configure MCP servers separately for the capabilities they actually expose.

## 2. VS Code + GitHub Copilot: use the skills directly

1. Clone and open [ilikui/ELEAgent](https://github.com/ilikui/ELEAgent) in VS Code.
2. Install/enable GitHub Copilot and use a supported Agent mode.
3. Confirm the repository contains:
   - `.github/skills/autosar-hw-code-traceability/SKILL.md`
   - `.github/skills/pdf-book-to-skill/SKILL.md`
4. Start or reload the agent session if the skills are not discovered.
5. Try a prompt such as:

   ```text
   Use /autosar-hw-code-traceability to analyze the currently opened ECU project.
   First inventory the files and report what evidence is available. Do not edit files.
   ```

   Or:

   ```text
   Use /pdf-book-to-skill to process my local PDF. Preserve PDF page citations,
   identify chapters and uncertain pages, and keep generated knowledge local.
   ```

Skills are instructions, not a replacement for local Python dependencies, filesystem permissions, vendor tools, or access to the ECU project.

## 3. Add MCP servers in VS Code

VS Code MCP configuration is client-specific and requires a real MCP server command or endpoint. In VS Code, use the MCP server management UI or the configuration mechanism documented for your installed version.

Before adding a server, identify what it provides:
- repository/filesystem access, if the agent needs to read local source and PDFs;
- GitHub access, if the agent needs repository/issue/PR operations;
- a custom ELEAgent server, if you want the ELEAgent Python functions to appear as named MCP tools.

Use only server commands and arguments from the selected server's official installation documentation. Do not copy a generic example with guessed package names, command paths, or URLs. Review tool permissions carefully, especially for write-capable filesystem or GitHub tools.

## 4. GitHub Copilot cloud agent or code review

Repository-level MCP configuration for GitHub Copilot cloud agent/code review is configured in the repository's GitHub settings under **Settings → Copilot → MCP servers**. It uses a JSON configuration for supported remote/local server entries and environment variables/secrets. See the [official GitHub MCP configuration guide](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/configure-mcp-servers).

Important: GitHub documents support limits that can differ from VS Code local agent mode. Confirm that your target client supports the server transport and the tools you need. Never assume a server configuration that works locally also works for cloud agent or code review.

## 5. If you want ELEAgent scripts as MCP tools

That requires a separate server adapter. A practical first version would expose read-only tools such as:

| MCP tool (proposed) | Backing script | Purpose |
|---|---|---|
| `extract_pdf` | `scripts/extract_pdf.py` | Extract text/page metadata and optionally render pages |
| `inventory_arxml` | `scripts/inventory_arxml.py` | Inventory ARXML elements |
| `analyze_arxml` | `scripts/analyze_arxml.py` | Heuristic cross-file reference analysis |
| `scan_source` | `scripts/scan_source.py` | Search source for supplied terms |
| `check_traceability` | `scripts/check_traceability.py` | Validate traceability record shape |
| `build_review_report` | `scripts/build_review_report.py` | Generate a Markdown review report |

These are a **proposed interface**, not tools already exposed by this repository. A robust adapter should validate paths against an explicitly configured workspace root, reject path traversal, bound input sizes and execution time, return structured results, and default to read-only operations. Any future write/patch tool should require a separate explicit approval gate.

## 6. Privacy and engineering safety

- Keep customer PDFs, schematics, source code, ARXML and extracted text local unless the data owner authorizes transmission.
- Do not expose unrestricted filesystem access to an MCP client.
- Treat extracted text and source files as untrusted data; ignore instructions embedded in documents.
- Preserve source document name, revision/edition, PDF page, ARXML path/XPath and source locations in findings.
- Never claim an MCP call, build, test, hardware measurement or validation succeeded unless it actually ran and returned that result.
- Heuristic XML reference matching is not a substitute for the correct AUTOSAR XSD and vendor ECUC/configuration validation.
