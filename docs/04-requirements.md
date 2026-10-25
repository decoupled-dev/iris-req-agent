# Requirements

The register stores every requirement. Export reads the register. Agents never overwrite baselined text.

## Identifiers

| Prefix | Use |
| --- | --- |
| `STK-` | Stakeholder need |
| `SYS-FUNC-` | Functional behavior |
| `SYS-PERF-` | Performance, timing, availability |
| `SYS-HMI-` | Dialogue, prompts, and display behavior |
| `SYS-COG-` | Cognitive companion behavior: context, memory, reasoning, proactivity, explanation, persona |
| `SYS-SAFE-` | Functional safety and SOTIF |
| `SYS-SEC-` | Cybersecurity |
| `SYS-PRIV-` | Privacy and data protection |
| `SYS-DIST-` | Driver distraction |

Numbers are stable. A new version of `SYS-FUNC-014` keeps that identifier. A rejected proposal does not reuse a number that was already accepted.

## Attributes

| Attribute | Rule |
| --- | --- |
| ID | One prefix from the table above |
| Title | Short name for the register |
| Statement | Stakeholder need in user language, or a system requirement with **shall** |
| Rationale | Why the item exists |
| Source | Agent finding, standard theme, or engineer |
| Category | Matches the ID prefix |
| Priority | Must, Should, or Could |
| Preliminary ASIL | QM, A, B, C, or D for `SYS-SAFE`; empty for other prefixes unless the safety agent links them |
| Cognitive capability | Zero or more IDs `COG-01`…`COG-20` from [09-cognitive-companion.md](09-cognitive-companion.md); required on `SYS-COG`, allowed on any prefix |
| Scenario | GIVEN / WHEN / THEN behaviour specification for behavioural requirements ([12-vehicle-context.md](12-vehicle-context.md)); empty for non-behavioural ones |
| Standard references | For example GDPR Art. 5, ISO 26262, ISO 21448, ISO/PAS 8800, ISO 21434, UN R155, ISO 15005, EU AI Act Art. 50 |
| Verification method | Test, Analysis, Inspection, or Demonstration |
| Acceptance criteria | Observable pass condition |
| State | See lifecycle below |
| Version | Integer, starting at 1 |
| Change note | What this version changed |
| Updated | Timestamp and author (person or agent id) |

System requirements use this statement shape:

> The voice assistant shall …

Stakeholder needs use:

> The driver shall be able to … / The occupant expects …

Behavioural requirements keep that one-line statement and add a structured scenario:

> **GIVEN** conditions on catalog vehicle signals
> **WHEN** one trigger: an utterance with an intent, a vehicle event such as IGN_ON or DOOR_OPEN, or a derived trigger
> **THEN** the companion's responses: ACT, CONFIRM_THEN_ACT, ASK, SUGGEST, INFORM, DEFER, or REFUSE

The statement is what the supplier contracts against. The scenario is the specification and the basis for the acceptance test.

## Lifecycle

| State | Meaning |
| --- | --- |
| Proposed | Agent output waiting in the inbox |
| Draft | Accepted by an engineer, still editable, included in export |
| In Review | Waiting on safety, privacy, cybersecurity, or systems review |
| Baselined | Agreed supplier text; changes only through a new accepted version |
| Rejected | Proposal or draft closed; kept for audit |
| Superseded | Previous version replaced by a newer accepted version |

Export includes **Draft**, **In Review**, and **Baselined**. It omits Proposed, Rejected, and Superseded items, and lists them only as history where the template asks for open or closed items.

## Continuous change

An engineer can add a requirement from the register at any time. The workbench assigns the next free ID for the chosen prefix, state Draft, version 1, and source “engineer”.

An engineer can edit a Draft or In Review item in place and increment the version with a change note.

A baselined item stays at its current statement until a proposal or an engineer edit is accepted as a new version. Acceptance:

- Stores the previous statement as Superseded
- Sets the new statement to the state the engineer chooses (Draft, In Review, or Baselined)
- Keeps the same ID

Rejection stores the proposal as Rejected and leaves the register item as it was.

## Reruns

A later pipeline run appends proposals. It does not delete requirements, versions, or prior runs. Synthesis must attach an update to an existing ID when the behavior already exists.

## Traceability

Each proposal stores the finding IDs it came from. The API refuses an agent proposal with no finding ID. The Excel traceability sheet and the Word verification matrix use that link. The compliance gate flags a baselined item with an empty source.

The **Cognitive capability** attribute is the second trace axis. It links a requirement to the capability catalog, and the gate uses it to compute the specified cognitive level.

## Examples

### Driver distraction

**ID:** `SYS-DIST-004`

**Statement:** The voice assistant shall complete a driving-task dialogue in a single spoken turn and shall not require the driver to look at a screen to finish that task.

**Rationale:** Visual-manual steps during a voice task are a known source of eyes-off-road time.

**Source:** Driver distraction agent, NHTSA visual-manual theme.

**Priority:** Must

**Verification method:** Test

**Acceptance criteria:** With the vehicle speed above the lockout threshold, the scripted navigation, media, and climate tasks finish by voice only, and the display does not present a list the driver must touch.

**State:** Draft until distraction review, then Baselined.

### Cognitive companion

**ID:** `SYS-COG-012`

**Statement:** The voice assistant shall offer a proactive suggestion only when it can name the vehicle or calendar signal that triggered it, and shall let the occupant dismiss that suggestion and disable its category by voice.

**Rationale:** Proactive help is valued only when it is timely, explainable, and easy to stop (VOC-06).

**Source:** Companion cognition agent, finding `find_cog_012`.

**Cognitive capability:** COG-12, COG-18

**Priority:** Must

**Verification method:** Test

**Acceptance criteria:** In the scripted low-range, traffic-delay, and calendar-departure scenarios, each suggestion states its trigger; “not now” dismisses it; “stop suggesting charging stops” prevents that category for the rest of the profile’s use until re-enabled.

**State:** Draft until distraction review, then Baselined.

### Behavioural, with scenario

**ID:** `SYS-COG-021`

**Statement:** The voice assistant shall respond to a cold-discomfort utterance by raising the climate setpoint of the speaker's zone by 2 °C and stating the change.

**Scenario:**

- **GIVEN** `ignition_state` = ON AND `speaker_seat` ≠ unknown AND `speaker_confidence` ≥ 0.8 AND `cabin_temp` < `setpoint_driver`
- **WHEN** UTTERANCE `thermal_discomfort.cold`: "I'm freezing"
- **THEN** ACT `climate_setpoint` [speaker zone] → +2 °C: "Warming your side up to {new_setpoint} degrees."

**Cognitive capability:** COG-01, COG-02, COG-04

**Verification method:** Test

**Acceptance criteria:** In the four-seat suite, "I'm freezing" from each seat raises only that zone's setpoint by 2 °C and the spoken response names the new value.
