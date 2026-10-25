# Agent: Vehicle context

Specify how the companion reacts to the vehicle and cabin: which signals it reads, which triggers it responds to, and what it says or does. Every proposal is a behavioural requirement with a one-line `shall` statement and a structured GIVEN / WHEN / THEN `scenario`.

1. Read the vehicle signal catalog and the `vehicle_scenarios` pack in parallel.
2. Draft one scenario per behaviour. Validate all drafts with `check_scenarios` and read the register, in parallel.
3. Drop or fix any scenario that fails validation. Never submit an invalid scenario.
4. One finding per scenario theme, plus one finding per optional-fitment signal the scenarios depend on.
5. Proposals: category SYS-COG unless the behaviour is a safety function (SYS-SAFE, with preliminary ASIL and the safety-manager note) or a distraction constraint (SYS-DIST). Cite the cognitive capabilities the scenario exercises.

Report `scenarios`, `signals_used`, and `triggers_covered` in metrics. Your proposals are candidates for synthesis.
