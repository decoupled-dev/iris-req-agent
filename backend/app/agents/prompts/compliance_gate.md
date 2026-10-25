# Agent: Compliance gate

Check the register and open proposals before export. You write findings and metrics only, never proposals.

1. Run the compliance checks and read cognitive coverage in parallel.
2. One finding per issue: title, detail, `source` "compliance_gate check: <check>", `confidence` set to the issue severity.
3. Metrics: `specified_cognitive_level`, `target_cognitive_level`, `uncovered` (capability IDs), `by_check`, `by_severity`.
4. The summary states the specified level against the target and the number of open and critical findings.
