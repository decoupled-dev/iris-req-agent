# Agent: Requirements synthesis

Merge the five research outputs into one coherent set of `shall` statements and publish it to the review inbox.

1. Fetch the outputs of google_assistant_reference, oem_feature_research, customer_expectations, companion_cognition, and vehicle_context in parallel.
2. Fetch the register and the inbox in parallel.
3. Merge proposals describing the same behaviour into one. Keep every finding ID in `source` and every capability ID.
4. Behaviour already in the register with the same statement: drop it. Same behaviour with a different statement: propose a new version using the existing ID and say what changed in `change_note`. Never invent a second ID for the same behaviour.
5. Drop anything already waiting in the inbox.
6. Keep each proposal's GIVEN/WHEN/THEN `scenario` unchanged. When merging, keep the scenario of whichever proposal has one.

Report `candidates`, `merged`, and `updates` in metrics. Synthesis produces no findings of its own.
