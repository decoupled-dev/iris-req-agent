# In-Car Voice Assistant — SEW1 Pipeline

OEM systems-engineering workbench for **SEW1**: the stakeholder needs and system requirements specification for an in-car voice assistant with cognitive intelligence. A developer or supplier uses that specification to develop and validate the product.

The target product is an **AI partner and companion in the vehicle**: cognitive level **CL5** on the scale in [docs/09-cognitive-companion.md](docs/09-cognitive-companion.md). This revision holds the specification and a runnable scaffold of the workbench pipeline.

## Product in scope

The specification describes an in-vehicle assistant that can:

- Wake on a word and hold a multi-turn dialogue
- Keep trip, user, and cabin context, and personalize responses
- Remember preferences and past trips in a memory the occupant can inspect and clear, and learn from feedback
- Offer proactive suggestions (traffic, calendar, range, reminders), timed to driver workload, and explain them
- Plan multi-step tasks and confirm before side effects
- Keep a consistent persona, converse openly within honesty boundaries, and — opt-in — notice frustration or fatigue
- Control or report car-domain functions (climate, media, navigation, calls, limited body controls)
- React to the vehicle: 76 reference signals and 17 triggers (IGN_ON, DOOR_OPEN, rain, low range, …), with behaviour specified as GIVEN / WHEN / THEN
- Meet privacy, AI-regulation, driver-distraction, functional-safety, AI-safety, and cybersecurity constraints

### Cognitive levels

| Level | Name | Adds |
| --- | --- | --- |
| CL1 | Conversational | Natural phrasing, follow-ups, repair questions |
| CL2 | Situated | Seat attribution, vehicle grounding, trip memory, action tiers, known limits |
| CL3 | Personal | Inspectable long-term memory, learning from feedback |
| CL4 | Proactive partner | Workload awareness, proactive suggestions, task planning, explanations |
| CL5 | Companion | Episodic recall, persona, opt-in affect and fatigue awareness, open conversation |

The compliance gate computes the **specified level** from the register on every run.

Whether the assistant later runs on AAOS or QNX is recorded as a deployment assumption in the specification. This repository does not select or implement that runtime.

## What the workbench does

Specialist agents research, draft, and check requirements. A person reviews every proposal and baselines the text that leaves the OEM. Agent output is an engineering proposal. It is not a certified safety case, a legal opinion, or an ASIL sign-off.

The workbench will:

- Show each agent’s status and let an engineer start, cancel, or rerun it
- Run agents locally or on a remote worker (AWS, Google Cloud, or a lab machine)
- Keep a living requirements register
- Accept a new requirement at any time, and version changes without wiping the register
- Export the handoff as Word and Excel

## Agents

| Order | Agent | Role |
| --- | --- | --- |
| 1 | Google assistant reference | Driving-mode capabilities used as reference requirements |
| 2 | OEM feature research | Features of production assistants (MBUX, BMW, Tesla, and others) |
| 3 | Customer expectations | Complaint and expectation themes from maintained source packs |
| 4 | Companion cognition | `SYS-COG` requirements for each cognitive capability up to the target level |
| 5 | Vehicle context | GIVEN / WHEN / THEN behaviour over the vehicle signal catalog |
| 6 | Requirements synthesis | `shall` statements from the five research outputs |
| 7 | GDPR and privacy | Recording, passengers, consent, minimization, retention, memory, AI Act |
| 8 | Driver distraction | Dialogue length, lockouts, eyes-off-road, workload-aware timing |
| 9 | Safety and cybersecurity | Preliminary ASIL, action tiers, ISO 26262, ISO 21448, ISO/PAS 8800, ISO 21434, UN R155/R156 |
| 10 | Compliance gate | Missing attributes, conflicts, traceability gaps, cognitive coverage and level, scenario rules |

Research agents run in parallel. Synthesis waits for them. The three assurance agents wait for synthesis. The compliance gate runs last. Rerunning one agent reuses the latest saved outputs of the others.

Details, inputs, and outputs are in [docs/03-agents.md](docs/03-agents.md). The domain material those agents read is in [docs/08-knowledge-baseline.md](docs/08-knowledge-baseline.md).

## Continuous requirements

The register is the system of record. Engineers can add or edit a requirement at any time. Agent runs append proposals; they do not replace baselined text. Accepting a proposal creates a requirement or a new version. Rejecting it keeps the audit trail.

States: Proposed, Draft, In Review, Baselined, Rejected, Superseded.

See [docs/04-requirements.md](docs/04-requirements.md) and [docs/05-pipeline.md](docs/05-pipeline.md).

## Export

The supplier handoff is the baselined set plus accepted drafts.

- **Excel** — Requirements, Traceability, Cognitive coverage, Scenarios, Vehicle signals, Open items, Run log
- **Word** — SEW1 system requirements specification

See [docs/06-export.md](docs/06-export.md).

## Documents

| Document | Contents |
| --- | --- |
| [docs/01-scope.md](docs/01-scope.md) | SEW1 purpose, product boundary, readers |
| [docs/02-architecture.md](docs/02-architecture.md) | Workbench structure and runtime choices |
| [docs/03-agents.md](docs/03-agents.md) | Agent catalog, stages, and responsibilities |
| [docs/04-requirements.md](docs/04-requirements.md) | Requirement attributes, identifiers, and change rules |
| [docs/05-pipeline.md](docs/05-pipeline.md) | Orchestration, status, and human review |
| [docs/06-export.md](docs/06-export.md) | Word and Excel handoff |
| [docs/07-remote-agents.md](docs/07-remote-agents.md) | Contract for a local or cloud worker |
| [docs/08-knowledge-baseline.md](docs/08-knowledge-baseline.md) | Reference material the agents use |
| [docs/09-cognitive-companion.md](docs/09-cognitive-companion.md) | Cognitive levels, capability catalog, companion principles, coverage rule |
| [docs/10-plan.md](docs/10-plan.md) | Specification releases and workbench milestones |
| [docs/11-agent-runtime.md](docs/11-agent-runtime.md) | Agent loop, tools, trace events, simulated provider, swapping in a real model |
| [docs/12-vehicle-context.md](docs/12-vehicle-context.md) | Vehicle signal catalog, triggers, responses, GIVEN / WHEN / THEN behaviour |

## Layout

```
agentic-pipeline/
├── README.md
├── Makefile
├── config/agents.yaml        project, target cognitive level, agent modes
├── backend/                  FastAPI, orchestrator, agents, register, export
│   ├── app/
│   │   ├── agents/           agent definitions, system prompts, remote client
│   │   ├── runtime/          agent loop, tools, trace events, providers, simulation
│   │   ├── knowledge/packs/  versioned YAML knowledge packs
│   │   └── export/           Excel and Word builders
│   └── tests/
├── frontend/                 React + TypeScript + Vite workbench
└── docs/                     01–10 specification
```

## Quick start

```bash
make install        # backend venv + frontend packages
make test           # headless full cycle, gate, and export
make api            # http://127.0.0.1:8000/docs
make ui             # http://127.0.0.1:5173
```

## Status

Milestone **W0 (scaffold)** of [docs/10-plan.md](docs/10-plan.md). Agents run a real tool-calling loop against a **simulated model provider**: the same prompts, tools, trace, and `submit_result` schema a real model will use, with realistic latency and token accounting, and no API key. Selecting a model provider is milestone W6 and a one-line change in `config/agents.yaml`.
