# Pipeline

The pipeline is a repeatable SEW1 cycle: research, synthesize, assure, review, baseline, export. Engineers run it when the program starts and again whenever a new requirement, a new market rule, or a new competitive finding appears.

## Control

From the control room an engineer can:

- Start the full cycle
- Start one agent
- Cancel a queued or running agent
- Rerun an agent after a failure or after the knowledge pack changes

The control room header shows **target** and **specified cognitive level** from the latest succeeded gate run.

Status on each card is idle, queued, running, succeeded, failed, or cancelled. The latest summary and timestamps stay visible after the run ends.

## Full cycle

1. Queue the five research agents and run them in parallel.
2. When all five have succeeded, queue synthesis.
3. When synthesis has succeeded, queue GDPR, driver distraction, and safety and cybersecurity in parallel.
4. When those three have succeeded, queue the compliance gate. The gate reports the specified cognitive level against the target.
5. Leave every synthesis and assurance proposal in the inbox. Do not baseline them automatically. Research candidates stay on their runs.

If a research agent fails, synthesis stays idle. The engineer fixes the cause or reruns that agent. Completed research runs remain available.

Cancelling an agent marks that run cancelled. Downstream agents do not start on a cancelled dependency during a full cycle. A later manual start may use the previous succeeded run of that dependency.

## Single-agent run

The engineer may run any agent alone.

- A research agent reads only its knowledge pack and the current register (companion cognition also reads the target level)
- Synthesis reads the latest **succeeded** research runs
- An assurance agent reads the latest succeeded synthesis run and the register
- The gate reads the register, open proposals, and the latest succeeded assurance runs

If a required prior run is missing, the API refuses the start and the control room states which agent must succeed first.

## Human review

The inbox lists proposals with their statement, rationale, source, and the finding they cite.

| Action | Result |
| --- | --- |
| Accept as Draft | Creates the requirement or a new version in Draft |
| Accept as In Review | Same, state In Review |
| Accept as Baselined | Same, state Baselined; reserved for reviewers allowed to baseline |
| Reject | Proposal becomes Rejected; register unchanged |
| Edit then accept | Engineer adjusts the statement, then accepts |

The register remains editable for Draft and In Review items outside the inbox. That is the continuous path: an engineer can add `SYS-FUNC-` (or any other prefix) without running an agent.

## What a rerun is allowed to change

| Object | On rerun |
| --- | --- |
| Baselined statement | Unchanged until a person accepts a new version |
| Open proposals from the previous run | Remain until accepted or rejected |
| New proposals | Appended |
| Findings | Stored on the new run |
| Run log | Appended |

## Export point

Export is available at any time. The file contains Draft, In Review, and Baselined items, gate findings that are still open, and the run log. A program should export the supplier issue only after the gate has succeeded and open findings are either closed or recorded as open points in the Word document.

## Roles

| Role | Allowed actions |
| --- | --- |
| Systems engineer | Run agents, add and edit requirements, accept to Draft or In Review, set the target cognitive level, export |
| Safety manager | Review `SYS-SAFE`, confirm or reject preliminary ASIL, baseline those items |
| Privacy reviewer | Review `SYS-PRIV`, and CL5 `SYS-COG` items that process memory or affect |
| Cybersecurity reviewer | Review `SYS-SEC` |
| Baseline owner | Move reviewed items to Baselined |

The first implementation may keep these roles as labels on the change note. Account management can follow later. The state machine above still applies: agent output cannot set Baselined by itself.
