# ELEAgent

Evidence-driven engineering assistant for embedded and automotive ECU projects.

## Initial module: AUTOSAR Hardware-to-Code Traceability

This repository hosts a read-only-first workflow for connecting circuit schematic PDFs and semiconductor documentation with AUTOSAR ARXML, ECUC configuration, MCAL/BSW/IoHwAb/RTE/SWC source code, and verification evidence.

### Safety model

- Analyze and report by default; do not edit project files until the user approves a concrete change plan.
- Never invent pins, electrical polarity, register values, requirements, tool results, or build outcomes.
- Preserve document revisions, PDF pages, ARXML paths/XPaths, source locations, and verification logs.
- Treat generated code through its authoritative configuration/generator workflow.
- Host tests and static checks do not prove ECU electrical behavior or functional-safety compliance.

See `.github/skills/autosar-hw-code-traceability/SKILL.md` for the workflow and `docs/` for the architecture and getting-started guide.
