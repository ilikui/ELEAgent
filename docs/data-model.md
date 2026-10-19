# Traceability data model

Each trace record should join five evidence groups plus a stable ID/status.

- requirement: requirement identifier, statement, source document and acceptance criteria
- hardware: signal/net, component reference, MCU pin, external circuit, schematic revision/page/region and review state
- chip: exact part/order code, document/revision/section/page, pin or register and applicable errata
- autosar: ARXML path, XPath, short name, module/container/parameter/value, variant and resolved references
- software: layer, file, symbol, line range, generated flag and authoritative generator source
- verification: test ID/method, status, command, exit code, log path, bench/HIL evidence and reviewer
- confidence/status/open_questions: explicit uncertainty and review state

Suggested status vocabulary: needs_human_review, evidence_incomplete, proposed, approved, implemented, software_verified, hardware_verified. Do not use a single PASS state to conflate these stages.

The schema is intentionally extensible because AUTOSAR variants and vendor configuration formats differ. The schema checks record shape only; it cannot establish the truth of evidence or semantic correctness.
