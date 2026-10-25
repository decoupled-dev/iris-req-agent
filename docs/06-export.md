# Export

Export is the supplier handoff. It is generated from the register at the moment of download. Two files are required: Excel for the working register, Word for the readable specification.

Included requirement states: Draft, In Review, Baselined.

The Word cover states the counts of each state so a supplier can see what is still in review.

## Excel workbook

### Sheet: Requirements

One row per included requirement, current version only.

Columns: ID, Version, State, Title, Statement, Rationale, Source, Category, Cognitive capability, Priority, Preliminary ASIL, ASIL note, Standard references, Verification method, Acceptance criteria, Change note, Updated.

### Sheet: Traceability

One row per link from a requirement to a finding.

Columns: Requirement ID, Requirement title, Finding ID, Agent, Finding title, Source.

### Sheet: Cognitive coverage

One row per capability in [09-cognitive-companion.md](09-cognitive-companion.md).

Columns: Capability ID, Faculty, Capability, Level, Covered (yes or no), Requirement IDs.

A header row states the target and the specified cognitive level.

### Sheet: Scenarios

One row per included requirement that has a GIVEN / WHEN / THEN scenario.

Columns: Requirement ID, Title, State, Given, When, Then, Signals, Cognitive capability.

### Sheet: Vehicle signals

One row per catalog signal ([12-vehicle-context.md](12-vehicle-context.md)).

Columns: Alias, Label, Domain, VSS path, VHAL property, Type, Unit, Access, Action tier, Availability, Privacy, Used by.

### Sheet: Open items

Rows for:

- Compliance-gate findings that are not closed
- Requirements in Draft or In Review
- Uncovered cognitive capabilities at or below the target level
- `SYS-SAFE` items whose ASIL note is still “to be confirmed by the safety manager”

Columns: Kind, ID, State, Summary, Owner hint.

### Sheet: Run log

One row per agent run.

Columns: Run ID, Agent, Mode (local or remote), Provider, Model, Turns, Input tokens, Output tokens, Status, Started, Finished, Summary.

## Word specification

**Title:** In-Car Voice Assistant with Cognitive Intelligence — System Requirements Specification (SEW1)

**Sections:**

1. **Document control** — program name, export time, register revision (highest requirement version timestamp), authoring tool name, state counts, target and specified cognitive level
2. **Scope** — product definition from [01-scope.md](01-scope.md), including the cognitive level scale and companion principles from [09-cognitive-companion.md](09-cognitive-companion.md)
3. **Context assumptions** — speech path, vehicle signals, display; AAOS or QNX recorded as an open deployment assumption, not as a design choice
4. **Vehicle context** — signal catalog status and per-domain summary, triggers, response types, and the number of behavioural requirements with scenarios
5. **Stakeholder needs** — all included `STK-` items
6. **System requirements by category** — functional, performance, HMI, then the groups below
7. **Cognitive companion** — `SYS-COG` items grouped by level, then the cognitive coverage table
8. **Privacy** — `SYS-PRIV` items and the note that lawful basis remains subject to privacy review
9. **Driver distraction** — `SYS-DIST` and linked HMI items
10. **Safety and cybersecurity** — `SYS-SAFE` and `SYS-SEC`, with preliminary ASIL and the safety-manager confirmation note on every safety item
11. **Verification matrix** — ID, verification method, acceptance criteria, state
12. **Open points** — the Open items sheet, in reading order
13. **Change record** — change notes for versions greater than 1 since the previous export, when a previous export timestamp is stored

Each requirement in the body shows ID, state, statement, its GIVEN / WHEN / THEN scenario when it has one, rationale, source, priority, and standard references.

## File names

- `SEW1-IVA-requirements-YYYYMMDD.xlsx`
- `SEW1-IVA-specification-YYYYMMDD.docx`

## Sharing

The files are the artifacts later stages receive. The workbench does not push them to a supplier portal in the first implementation. The engineer downloads and distributes them.

## Regeneration

A new export after an accepted requirement, a new version, or a closed open item produces a new file. Older downloads are not rewritten.
