# Cognitive companion

SEW1 specifies an assistant that behaves as a partner in the vehicle, not a command parser. This document turns “cognitive intelligence” into a level scale, a capability catalog, and coverage rules the compliance gate can check. Every capability here must end up as at least one traced, verifiable requirement before the program can claim the level.

## Cognitive levels

Levels are cumulative. A level is **specified** when every capability of that level and of all lower levels is covered (see [Coverage rule](#coverage-rule)).

| Level | Name | The occupant experiences | Capabilities |
| --- | --- | --- | --- |
| CL0 | Command | Fixed phrases, one turn, no memory | — |
| CL1 | Conversational | Natural phrasing, several intents in one sentence, follow-ups without repeating the subject, a repair question when unsure | COG-04, COG-05, COG-06 |
| CL2 | Situated | The assistant knows who is speaking, what the car is doing, and what was said earlier in the trip; vehicle facts are never invented; it says what it cannot do offline | COG-01, COG-02, COG-07, COG-11, COG-14, COG-20 |
| CL3 | Personal | Preferences, routines, and places are remembered per profile, can be inspected and cleared, and improve from feedback | COG-08, COG-19 |
| CL4 | Proactive partner | The assistant anticipates needs from named signals, plans multi-step tasks, times its speech to driver workload, and explains why it suggested something | COG-03, COG-10, COG-12, COG-13, COG-18 |
| CL5 | Companion | Continuity across trips, a consistent persona, opt-in awareness of frustration or fatigue, and open conversation within honesty boundaries | COG-09, COG-15, COG-16, COG-17 |

**Program target: CL5.** CL0–CL4 capabilities are proposed as **Must**. CL5 capabilities are proposed as **Should**, default off where they process affect or biometric data, and stay In Review until privacy and AI-regulation review closes (see [Companion principles](#companion-principles)).

## Capability catalog

Faculty groups the capability for readers. The ID is what a requirement cites in its **Cognitive capability** attribute ([04-requirements.md](04-requirements.md)).

| ID | Faculty | Capability | Level | Requirement direction | Assurance link |
| --- | --- | --- | --- | --- | --- |
| COG-01 | Perceive | Speaker and seat attribution | CL2 | `SYS-COG` attribute each utterance to a seat; act in that seat’s zone | VOC-07, `SYS-SAFE` for driver-only functions |
| COG-02 | Perceive | Vehicle and cabin state grounding (speed, range, climate, occupancy, guidance active) | CL2 | `SYS-COG` answers and decisions use current vehicle signals | VOC-08 |
| COG-03 | Perceive | Driver workload estimate from vehicle signals (manoeuvre, speed band, active guidance, incoming call) | CL4 | `SYS-COG` / `SYS-DIST` workload state available to dialogue | ISO 15005 |
| COG-04 | Understand | Natural phrasing, paraphrase, multi-intent utterances | CL1 | `SYS-FUNC` / `SYS-COG` | VOC-01 |
| COG-05 | Understand | Multi-turn reference resolution (“there”, “call her”, “a bit warmer”) | CL1 | `SYS-COG` context survives follow-ups | — |
| COG-06 | Understand | Ambiguity and low-confidence detection with a spoken repair question | CL1 | `SYS-COG` / `SYS-SAFE` no actuation on low confidence | VOC-01, VOC-04, ISO 21448 |
| COG-07 | Remember | Trip memory: entities and tasks from the current trip | CL2 | `SYS-COG` | — |
| COG-08 | Remember | Long-term personal memory (preferences, routines, places) per profile; inspectable, editable, clearable by voice and on screen while parked | CL3 | `SYS-COG` / `SYS-PRIV` | GDPR Art. 5, 17, 25 |
| COG-09 | Remember | Episodic recall across trips (“the café we stopped at last Tuesday”) | CL5 | `SYS-COG` / `SYS-PRIV` retention bound | GDPR Art. 5 |
| COG-10 | Reason | Multi-step task planning (charging stop + reservation + ETA message) with a spoken plan and confirmation before side effects | CL4 | `SYS-COG` | VOC-04 |
| COG-11 | Reason | Grounded answers: vehicle facts only from signals or the owner’s manual; says “I don’t know” rather than invent | CL2 | `SYS-COG` / `SYS-SAFE` | VOC-08, ISO/PAS 8800 |
| COG-12 | Anticipate | Proactive suggestions tied to a signal the assistant names; dismissible, rate-limited, can be turned off per category | CL4 | `SYS-COG` / `SYS-HMI` | VOC-06 |
| COG-13 | Anticipate | Workload-aware timing: non-urgent speech deferred during high-demand driving | CL4 | `SYS-DIST` / `SYS-COG` | ISO 15005, NHTSA |
| COG-14 | Act | Tool execution through the vehicle interface by permission tier: information, comfort, high-impact (confirm), prohibited | CL2 | `SYS-COG` / `SYS-SAFE` | VOC-04, ISO 26262 |
| COG-15 | Relate | Consistent persona, name, and voice; adjustable verbosity and formality per profile | CL5 | `SYS-HMI` / `SYS-COG` | — |
| COG-16 | Relate | Opt-in awareness of frustration (from dialogue behaviour) and fatigue (from the driver-monitoring system when fitted), with adapted tone and break suggestions | CL5 | `SYS-COG` / `SYS-PRIV` / `SYS-DIST` | GDPR Art. 9, EU AI Act |
| COG-17 | Relate | Open-domain conversation and companionship within honesty boundaries | CL5 | `SYS-COG` | EU AI Act Art. 50 |
| COG-18 | Explain | “Why did you suggest that?” and “what do you remember about me?” answered in plain speech | CL4 | `SYS-COG` | GDPR Art. 13, VOC-08 |
| COG-19 | Learn | Adapts from explicit feedback and accepted or declined suggestions, per profile, reversible | CL3 | `SYS-COG` / `SYS-PRIV` | GDPR Art. 25 |
| COG-20 | Self-model | States its own limits: offline capability, confidence, unavailable domains | CL2 | `SYS-COG` / `SYS-PERF` | VOC-02, VOC-08 |

## Action permission tiers

COG-14 and COG-10 rely on one tiering. The safety agent proposes the tier for each car-domain function; the safety manager confirms it.

| Tier | Examples | Rule |
| --- | --- | --- |
| Information | Range, ETA, tyre pressure, manual answers | Execute; answer only from grounded sources |
| Comfort | Climate, seat heat, media, ambient light | Execute in the speaker’s zone; undoable by voice |
| High-impact | Windows, sunroof, locks, child lock, eCall cancel, sending a message | Spoken confirmation; speed and occupancy conditions |
| Prohibited | Engaging or disengaging driver assistance, drive mode, anything with vehicle-motion authority | Not available by voice unless a dedicated confirmed command is separately specified |

## Companion principles

These apply to every `SYS-COG` requirement and are what reviewers check CL5 proposals against.

1. **Road first.** Driving demand outranks conversation. The assistant yields, shortens, or defers.
2. **Honest identity.** The assistant states that it is an AI when asked and at first use. It does not claim feelings, experiences, or a human identity.
3. **No manipulation.** Persona, memory, and affect awareness are not used to persuade toward purchases or to increase engagement time. Commercial suggestions, if any, are labelled and can be turned off.
4. **Occupant owns memory.** Everything remembered can be listed, corrected, and deleted. Guest and no-memory modes exist.
5. **Grounded, not guessed.** Vehicle and safety facts come from signals or documentation. Uncertainty is spoken.
6. **Affect is opt-in.** Frustration and fatigue awareness is off by default, explained before enabling, and does not use voice biometrics unless a lawful basis is recorded.
7. **Cabin, not only driver.** Passengers and children are heard. Their speech is not used for personalization without their own profile.

**Regulatory note for reviewers (to be confirmed by privacy and legal review):** inferring emotion from voice characteristics may be emotion recognition under the EU AI Act. In fleet or company vehicles the cabin can be a workplace, where such inference is restricted. The default design for COG-16 therefore infers frustration from dialogue behaviour (repeats, corrections, aborts) and takes fatigue only from a separately specified driver-monitoring function.

## Coverage rule

A capability is **covered** when the register holds at least one requirement that:

- cites the capability in **Cognitive capability**
- is in state Draft, In Review, or Baselined
- has a verification method and acceptance criteria

The **specified cognitive level** is the highest CLn for which every capability at CL1…CLn is covered. The compliance gate computes it on each run, reports uncovered capabilities as findings, and the control room and export show it next to the target.

## Verification approach

Acceptance criteria for `SYS-COG` items should reference a scripted cognitive evaluation suite. The suite is a downstream verification work product; SEW1 names the measures so suppliers can plan for them.

| Measure | Applies to | Proposed initial target (to be confirmed) |
| --- | --- | --- |
| Multi-turn task success | COG-04, 05, 07, 10 | ≥ 90 % of scripted scenarios |
| Repair instead of guess | COG-06 | 100 % of below-threshold scenarios ask a question |
| Unconfirmed high-impact actuation | COG-14 | 0 occurrences |
| Invented vehicle status | COG-11 | 0 occurrences in the grounding suite |
| Proactive speech during high workload | COG-13 | 0 non-urgent prompts in high-demand segments |
| Suggestion dismiss rate | COG-12 | Reported per category; threshold set by the program |
| Memory inspection and deletion | COG-08, 18 | All stored items listed; deletion effective before next trip |
| AI disclosure | COG-17 | Disclosed at first use and on request in every scenario |
| End of speech to first audio | All | p90 ≤ 1.2 s on-device, ≤ 2.0 s cloud |

## How the pipeline uses this document

- The **companion cognition** agent reads the catalog as a knowledge pack and proposes `SYS-COG` requirements per capability ([03-agents.md](03-agents.md)).
- **Synthesis** keeps the capability ID when merging.
- **Privacy**, **distraction**, and **safety** agents add constraints to COG-08, 09, 13, 14, 16.
- The **compliance gate** applies the coverage rule and reports the specified level.
- **Export** prints the target and specified level in document control and adds a cognitive coverage sheet ([06-export.md](06-export.md)).
