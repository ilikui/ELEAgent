"""Read-only-first MCP server for ELEAgent engineering analysis.

Run with: python mcp_server.py
The server uses stdio transport and confines user-supplied paths to ELEAGENT_WORKSPACE.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from mcp.server.fastmcp import FastMCP

REPO_ROOT = Path(__file__).resolve().parent
SCRIPTS = REPO_ROOT / ".github" / "skills" / "autosar-hw-code-traceability" / "scripts"
DEFAULT_WORKSPACE = Path.cwd()
mcp = FastMCP("eleagent")


def workspace_root() -> Path:
    raw = os.environ.get("ELEAGENT_WORKSPACE")
    root = Path(raw).expanduser() if raw else DEFAULT_WORKSPACE
    return root.resolve()


def safe_path(value: str, *, must_exist: bool = True, want_dir: bool | None = None) -> Path:
    """Resolve a user path inside the configured workspace; reject traversal."""
    if not value or not value.strip():
        raise ValueError("Path must not be empty.")
    supplied = Path(value)
    if supplied.is_absolute():
        raise ValueError("Use a path relative to ELEAGENT_WORKSPACE, not an absolute path.")
    root = workspace_root()
    candidate = (root / supplied).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError("Path escapes ELEAGENT_WORKSPACE; request rejected.") from exc
    if must_exist and not candidate.exists():
        raise FileNotFoundError(f"Path does not exist inside workspace: {value}")
    if want_dir is True and candidate.exists() and not candidate.is_dir():
        raise ValueError(f"Expected a directory: {value}")
    if want_dir is False and candidate.exists() and not candidate.is_file():
        raise ValueError(f"Expected a file: {value}")
    return candidate


def run_script(script_name: str, args: Sequence[str], timeout: int = 120) -> str:
    script = (SCRIPTS / script_name).resolve()
    if not script.is_file() or script.parent != SCRIPTS.resolve():
        raise RuntimeError(f"Trusted script not found: {script_name}")
    completed = subprocess.run(
        [sys.executable, str(script), *args],
        cwd=str(workspace_root()),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    output = (completed.stdout or "").strip()
    errors = (completed.stderr or "").strip()
    result = {
        "tool": script_name,
        "exit_code": completed.returncode,
        "stdout": output[-12000:],
        "stderr": errors[-6000:],
        "workspace": str(workspace_root()),
        "note": "Text matches and heuristic ARXML results are evidence-discovery aids, not proof of hardware behavior or AUTOSAR semantic validity.",
    }
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def extract_pdf(pdf_path: str, render_pages: bool = False, min_chars: int = 40) -> str:
    """Extract selectable PDF text per page and write a metadata manifest.

    pdf_path is relative to ELEAGENT_WORKSPACE. Output is written under
    engineering/extracted/pdf_text and, when requested, engineering/extracted/page_images.
    Low-text pages are flagged for visual review; OCR is not performed.
    """
    pdf = safe_path(pdf_path, want_dir=False)
    if pdf.suffix.lower() != ".pdf":
        raise ValueError("pdf_path must point to a .pdf file.")
    if min_chars < 0 or min_chars > 10000:
        raise ValueError("min_chars must be between 0 and 10000.")
    output = safe_path("engineering/extracted/pdf_text", must_exist=False, want_dir=True)
    args = [str(pdf), "--out", str(output), "--min-chars", str(min_chars)]
    if render_pages:
        args.append("--render")
    return run_script("extract_pdf.py", args, timeout=180)


@mcp.tool()
def analyze_arxml(arxml_path: str, output_path: str = "engineering/traceability/arxml_analysis.json") -> str:
    """Inventory ARXML names and candidate references. This is heuristic, not XSD/ECUC validation."""
    source = safe_path(arxml_path, want_dir=None)
    if source.is_file() and source.suffix.lower() != ".arxml":
        raise ValueError("arxml_path must be an .arxml file or a directory containing ARXML files.")
    output = safe_path(output_path, must_exist=False, want_dir=False)
    return run_script("analyze_arxml.py", [str(source), "--out", str(output)])


@mcp.tool()
def scan_source(source_path: str = ".", terms: str = "", output_path: str = "engineering/traceability/source_hits.json") -> str:
    """Search C/C++ source and supported configuration files for comma-separated terms."""
    if not terms.strip():
        raise ValueError("Supply at least one comma-separated search term.")
    source = safe_path(source_path, want_dir=True)
    output = safe_path(output_path, must_exist=False, want_dir=False)
    return run_script("scan_source.py", [str(source), "--terms", terms, "--out", str(output)])


@mcp.tool()
def check_traceability(traceability_json: str) -> str:
    """Validate traceability JSON structure and report unresolved evidence; does not prove correctness."""
    file_path = safe_path(traceability_json, want_dir=False)
    if file_path.suffix.lower() != ".json":
        raise ValueError("traceability_json must point to a .json file.")
    return run_script("check_traceability.py", [str(file_path)])


@mcp.tool()
def build_review_report(
    traceability_json: str,
    output_path: str = "engineering/reports/review_report.md",
) -> str:
    """Build a Markdown evidence-review report from traceability JSON."""
    file_path = safe_path(traceability_json, want_dir=False)
    output = safe_path(output_path, must_exist=False, want_dir=False)
    if file_path.suffix.lower() != ".json":
        raise ValueError("traceability_json must point to a .json file.")
    return run_script("build_review_report.py", [str(file_path), "--out", str(output)])


@mcp.tool()
def export_pin_excel(inventory_json: str, output_path: str = "engineering/reports/pin_signal_inventory.xlsx") -> str:
    """Export a hardware inventory JSON to an Excel PIN/signal workbook.

    Includes MCU vs I/O-expander/device classification, component inventory,
    nets/cross-sheet links and field definitions. Formats known evidence only.
    """
    source = safe_path(inventory_json, want_dir=False)
    if source.suffix.lower() != ".json":
        raise ValueError("inventory_json must point to a .json file.")
    output = safe_path(output_path, must_exist=False, want_dir=False)
    if output.suffix.lower() != ".xlsx":
        raise ValueError("output_path must end with .xlsx.")
    return run_script("export_pin_excel.py", [str(source), "--out", str(output)])


@mcp.tool()
def get_workspace_info() -> str:
    """Return the configured workspace root and available read-only analysis tools."""
    root = workspace_root()
    return json.dumps({
        "workspace": str(root),
        "workspace_exists": root.is_dir(),
        "server": "ELEAgent",
        "transport": "stdio",
        "tools": ["extract_pdf", "analyze_arxml", "scan_source", "check_traceability", "build_review_report", "export_pin_excel", "get_workspace_info"],
        "write_policy": "No source/ARXML/ECUC/generated-code editing tools are exposed. Analysis tools may write reports/extraction output only within the workspace.",
    }, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")
