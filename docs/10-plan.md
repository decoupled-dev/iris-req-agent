# Plan

Two tracks run together. The **specification track** grows the SEW1 baseline until the register covers the target cognitive level. The **workbench track** builds the tool that produces it. The scaffold in `backend/` and `frontend/` is milestone W0.

## Specification track

| Release | Specified level | Content | Exit criteria |
| --- | --- | --- | --- |
| S1 | CL2 Situated | Core dialogue, vehicle grounding, seat attribution, action tiers, offline behaviour; the vehicle signal catalog replaced by the OEM signal database; utterance and vehicle-event scenarios; privacy, distraction, and safety baselines for those | Gate reports CL2; every `SYS-SAFE` item has a preliminary ASIL awaiting confirmation; no open gate finding of kind *conflict* |
| S2 | CL4 Proactive partner | Personal memory and learning, proactive suggestions, workload-aware timing, task planning, explanations; derived-trigger scenarios (low range, sustained discomfort, long drive) | Gate reports CL4; COG-08 and COG-19 items reviewed by privacy; COG-13 items reviewed by distraction |
| S3 | CL5 Companion | Episodic recall, persona, opt-in affect and fatigue awareness, open conversation within the companion principles | Gate reports CL5; COG-16 and COG-17 items closed by privacy and AI-regulation review or recorded as open points in the Word export |

Each release ends with an export issued to the supplier. Later releases add versions; they do not reset the register.

### Review cadence

- Systems engineering triages the inbox after every full cycle.
- Safety, privacy, and cybersecurity review their prefixes before each release export.
- The knowledge packs are versioned; a pack change triggers a rerun of the agents that read it.

## Workbench track

| Milestone | Delivers | Done when |
| --- | --- | --- |
| W0 Scaffold | Repository layout, agent contract, provider-neutral agent loop with tools and run traces, simulated provider with a policy per agent, orchestrator DAG, SQLite register, API, Word and Excel exporters, six-page workbench UI, tests | `make test` passes; a full cycle runs with no key and produces traces, proposals, gate findings, the specified level, and both export files |
| W1 Register | Accept, reject, edit-then-accept, versioning and supersede, ID allocation, role labels on change notes | Lifecycle rules in [04-requirements.md](04-requirements.md) covered by tests |
| W2 Agents | Richer pack mapping, synthesis deduplication across sources, cognitive coverage on every proposal | Each agent’s rules in [03-agents.md](03-agents.md) have a test; gate reports CL5 on the shipped packs after accepting all proposals |
| W3 Workbench UI | Control room, register, inbox, export pages fully wired | An engineer can run the whole cycle without the API docs page |
| W4 Export | Templates matching [06-export.md](06-export.md) section by section | Generated files open in Word and Excel and pass a structure check |
| W5 Remote workers | HTTP worker client, polling, cancel, auth from env | A reference worker in `backend/worker/` passes the contract test in [07-remote-agents.md](07-remote-agents.md) |
| W6 Model provider | Implement the selected adapter (Claude API, Claude on Vertex AI, Gemini, or OpenAI-compatible); evaluation comparing provider output with simulated output on the shipped packs | Switching `runtime.provider` is the only change; every agent still finishes with a valid `submit_result`; simulated stays the test default |

## Risks

| Risk | Mitigation |
| --- | --- |
| CL5 affect features blocked by regulation in some markets | Keep COG-16 opt-in and severable; gate reports CL5 coverage separately from market approval |
| “Companion” drifts into engagement optimization | Companion principles are a gate checklist item for every `SYS-COG` proposal |
| Agents produce plausible but unsourced requirements | Proposals without finding IDs are rejected by the API; the gate flags empty sources |
| Reference signal catalog diverges from the OEM signal database | Scenarios name signals by alias; replacing the catalog re-validates every scenario through the gate, so mismatches surface as findings |
| Proactive behaviour raises distraction | COG-12 always ships with COG-13; the gate flags a COG-12 item with no linked `SYS-DIST` item |
| Latency targets set too early | Performance values are proposals marked “to be confirmed” until the speech path is selected |
