# Scope

## SEW1

SEW1 is the first systems-engineering work product for this program: stakeholder needs and the system requirements specification. Downstream development and validation use this document as the agreed requirement baseline.

The workbench produces and maintains that baseline. It does not design software architecture, write implementation code, or execute verification tests. Those belong to later work products.

## Product

**Name:** In-car voice assistant with cognitive intelligence.

**Ambition:** An AI partner and companion in the vehicle — situated, personal, proactive, and trustworthy — specified to cognitive level **CL5** on the scale in [09-cognitive-companion.md](09-cognitive-companion.md), with driving safety and occupant control taking priority over companionship.

**Users:** Driver and passengers, through speech. Service and engineering users may query status. They do not receive a workshop diagnostic tool in this scope.

**Capabilities the specification must cover:**

- Wake word, barge-in, and multi-turn dialogue
- Context across a trip, a user profile, and the current cabin
- Personalization and proactive suggestions grounded in that context
- Long-term memory the occupant can inspect and clear, learning from feedback, and explanations of why the assistant did something
- Multi-step task planning with confirmation before side effects
- Workload-aware timing of speech
- A consistent persona, open conversation within honesty boundaries, and opt-in awareness of frustration and fatigue
- Navigation, media, phone, and messaging read-out
- Car-domain commands and status (climate, seats, windows, lights, charge, range)
- Degraded and offline behavior when cloud speech is unavailable
- Guest, valet, and privacy modes
- Constraints from privacy law, AI regulation, driver distraction, functional safety, SOTIF, AI safety, and cybersecurity

## Deployment assumption

The assistant may be integrated at the AAOS layer or at the QNX layer. The specification records the behaviors the assistant must provide in either case. Selection of the runtime, the speech engine, and the cloud region is outside SEW1.

Interface assumptions that belong in the specification:

- A speech capture and playback path exists in the vehicle
- Vehicle signals needed for context and for safety interlocks are available to the assistant through a defined vehicle interface
- A human-machine display may show transcripts and confirmations, and remains subject to driver-distraction rules

## Readers

| Reader | Use of SEW1 |
| --- | --- |
| OEM systems engineering | Owns the baseline and the review workflow |
| OEM safety, cybersecurity, and privacy | Review assurance requirements before baseline |
| Supplier or internal developer | Implements and verifies against the baselined `shall` statements |
| Validation | Builds the verification matrix from the same register |

## Authority of agent output

Agents draft findings and proposed requirements. A named reviewer moves text to **Baselined**. Until that transition, the text is not part of the supplier handoff.

Preliminary ASIL values are engineering proposals marked **to be confirmed by the safety manager**. They are not an ISO 26262 safety-case result.

Privacy and AI-regulation requirements are engineering requirements aligned to GDPR and EU AI Act themes. They are not a legal determination of lawful basis for a specific market.

## Out of scope for this repository revision

- Production implementation of the workbench; this revision holds a runnable scaffold only (see [10-plan.md](10-plan.md))
- Live crawling of forums or competitor sites
- Certified safety analysis, penetration testing, or legal review
- The voice-assistant product itself
