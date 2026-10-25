# Knowledge baseline

This is the versioned material local agents read. It is public product behavior, regulatory themes, and recurring owner-reported expectations. It is input to proposals. Reviewers still baseline every requirement.

A remote customer-expectations worker may replace the “Customer themes” section with findings from an approved research service. The finding shape stays the one in [07-remote-agents.md](07-remote-agents.md).

Pack version: **2026-10-25**. Machine-readable packs live in `backend/app/knowledge/packs/`; this document is their reviewed source.

## Google assistant reference

Driving-related capabilities to treat as reference behavior:

| Theme | Reference behavior | Requirement direction |
| --- | --- | --- |
| Navigation | Set a destination, add a stop, ask remaining time and traffic, by voice | `SYS-FUNC` navigation dialogue |
| Media | Play, pause, skip, search music and radio by voice | `SYS-FUNC` media |
| Calls and messages | Call a contact, read incoming messages aloud, reply by voice | `SYS-FUNC` and `SYS-DIST` (read-out, no typing) |
| Car controls | Climate setpoint, fan, heated seats, windows, where the vehicle exposes them | `SYS-FUNC` with safety interlocks |
| Offline limits | Many cloud features are unavailable without connectivity; on-device commands should be named | `SYS-PERF` degraded mode |
| Assistant identity | The OEM assistant is specified on its own; Google behavior is a reference, not a branded dependency | Source note on each proposal |

## Production assistants

### Mercedes-Benz MBUX Voice Assistant

- Hey Mercedes wake word and barge-in
- Seat-aware commands (the speaking seat’s climate and comfort)
- Over-the-air growth of domains the assistant understands
- Natural follow-up questions without repeating the wake word in a short window
- Car manual and how-to answers spoken in the vehicle

### BMW Intelligent Personal Assistant

- Wake word and optional custom wake behavior
- Vehicle function explanations and pro tips
- Driver-profile routines and learned climate or navigation habits
- In-car assistant distinct from the driver’s phone assistant

### Tesla voice commands

- Large set of vehicle-control phrases, including navigation and comfort
- Continuous addition of commands through software updates
- Limited small talk; emphasis on reliable command execution

### Hyundai and Kia assistant

- Navigation, media, weather, and vehicle-status questions
- Linked calendar and connected-service features when the account is signed in
- Home-to-car continuation of some assistant tasks where the brand offers it

Comparison proposals should say whether the OEM will match the feature, limit it while driving, or exclude it. Exclusion is a valid requirement when distraction or safety requires it.

## Customer themes

Maintained themes. The first implementation does not scrape forums.

| ID | Theme | Expectation |
| --- | --- | --- |
| VOC-01 | Misrecognition | Names, streets, and accented speech are understood, and the assistant asks a clarifying question instead of acting on a low-confidence guess |
| VOC-02 | Offline use | Essential climate, media, and phone commands still work without a network |
| VOC-03 | Recording privacy | A visible or spoken indication when audio is captured, a mute that cuts the microphone, and a way to delete stored voice data |
| VOC-04 | Unintended actions | Windows, locks, and driving functions are not acted on from a partial or overheard phrase |
| VOC-05 | Distraction | Tasks finish by voice; the assistant does not push the driver to a touch list while the vehicle is moving |
| VOC-06 | Proactive help | Timely warnings (traffic, low range, calendar departure) that the driver can dismiss and can turn off |
| VOC-07 | Passengers | A passenger can control passenger-zone comfort without overriding the driver |
| VOC-08 | Trust | The assistant states when it did not understand and does not invent vehicle status |

These become `STK-` needs and traced system requirements.

## Companion cognition

The capability catalog, cognitive levels, action tiers, companion principles, and verification measures are in [09-cognitive-companion.md](09-cognitive-companion.md). The companion cognition agent reads that catalog as this pack section. Every capability needs at least one `SYS-COG` (or linked) requirement for the program to claim its level.

Reference behaviour from production assistants that maps to the catalog:

| Observed behaviour | Capability |
| --- | --- |
| Follow-up without repeating the wake word (MBUX) | COG-05 |
| Seat-aware commands (MBUX) | COG-01 |
| Learned climate or navigation habits (BMW) | COG-08, COG-19 |
| Vehicle function explanations (BMW, MBUX) | COG-11 |
| Range and calendar departure prompts (several brands) | COG-12 |

## Privacy themes

Map to `SYS-PRIV`. Cite the theme; privacy review confirms market applicability.

| Theme | GDPR anchor | Requirement intent |
| --- | --- | --- |
| Purpose limitation | Art. 5 | Voice audio is processed for the requested assistant task and the stated improvement purpose |
| Data minimization | Art. 5 | Raw audio is not kept when a transcript or a command result is enough |
| Transparency | Art. 13 | Occupants are told what is captured, where it is processed, and how long it is kept |
| Lawful basis | Art. 6 | Each processing purpose has a recorded basis before baseline |
| Special-category care | Art. 9 | Biometric voice identification, if used, is specified separately and stays off until the basis is recorded |
| Privacy by design | Art. 25 | Mute, guest mode, and no-recording mode exist as default cabin controls |
| Security of processing | Art. 32 | Voice data in transit and at rest is protected |
| Retention and deletion | Art. 5, Art. 17 | Stored utterances and voice profiles can be deleted by the account holder |
| Personal memory | Art. 5, Art. 15, Art. 17 | Long-term and episodic memory is listed on request, correctable, deletable, and bounded in retention |
| AI disclosure | EU AI Act Art. 50 | Occupants are told they are interacting with an AI system |
| Emotion inference | EU AI Act Art. 5, Art. 50; GDPR Art. 9 | Affect awareness is opt-in, avoids voice biometrics by default, and is reviewed for workplace (fleet) use |

Passenger speech and guest sessions are in scope because the microphone hears the cabin, not only the driver.

## Driver distraction themes

Map to `SYS-DIST` and `SYS-HMI`.

| Theme | Reference | Requirement intent |
| --- | --- | --- |
| Eyes off road | NHTSA visual-manual distraction guidelines | A voice task does not require a glance at a list or a touch confirmation while driving |
| Dialogue management | ISO 15005 | Spoken prompts are short, interruptible, and paced so the driver can return attention to the road |
| Lockout | OEM driving policy | Text entry, map browsing, and multi-screen choices are unavailable above the configured speed |
| High-impact confirmation | Customer theme VOC-04 | Window, lock, and assistance commands require an explicit spoken confirmation |
| Passenger tasks | Seat-aware HMI | Passenger tasks do not place a visual demand on the driver |

## Safety and cybersecurity themes

Preliminary classes are proposals. Every `SYS-SAFE` item keeps the note **to be confirmed by the safety manager**.

| Item | Preliminary ASIL | Standards | Intent |
| --- | --- | --- | --- |
| Navigation, media, general dialogue | QM | ISO 26262 (QM) | No vehicle-motion authority |
| Wrong or missed emergency call | B, candidate | ISO 26262, ISO 21448 | eCall or roadside assistance must not be dropped or invoked by an unrelated phrase |
| Window, sunroof, and child-lock commands | B, candidate | ISO 26262 | Motion of glazing and lock state need confirmation and speed or occupancy conditions |
| Voice engagement of driver assistance | B, candidate | ISO 26262, ISO 21448 | Assistance mode changes are out of casual dialogue unless a dedicated confirmed command exists |
| Misunderstood command | QM to A, candidate | ISO 21448 | Low confidence yields a question, not an actuation |
| Invented vehicle status or wrong manual answer | QM to A, candidate | ISO 21448, ISO/PAS 8800 | Vehicle facts come only from signals or documentation; uncertainty is spoken |
| Planner executes a high-impact step without confirmation | B, candidate | ISO 26262, ISO/PAS 8800 | Multi-step plans pause for confirmation before each high-impact step |
| Spoofed or injected voice command | — | ISO 21434, UN R155 | Wake-word and command path resists replay and remote injection; security goals are stated for the item |
| Model and skill updates | — | UN R156, ISO 21434 | Updates are authentic, and a failed update leaves the previous assistant usable |
| Prompt injection via messages, calendar, or web content | — | ISO 21434, UN R155 | Content read aloud or summarized cannot issue vehicle commands or change memory |

Cybersecurity items use `SYS-SEC` and do not carry an ASIL. They reference UN R155 threat themes: spoofing, tampering with commands, and information disclosure of cabin audio.

## Standards index

| Identifier | Use in this baseline |
| --- | --- |
| GDPR | Privacy themes for cabin audio and profiles |
| ISO 15005 | Dialogue management while driving |
| NHTSA driver distraction guidelines | Visual-manual limits for in-vehicle tasks |
| ISO 26262 | Functional safety; preliminary ASIL only |
| ISO/PAS 8800 | Safety of AI elements in road vehicles: grounding, planner confirmation |
| EU AI Act (Regulation (EU) 2024/1689) | AI disclosure and emotion-recognition themes |
| ISO 21448 | Safety of the intended functionality for misrecognition |
| ISO 21434 | Cybersecurity engineering |
| UN R155 | Cybersecurity management, threat themes |
| UN R156 | Software update of assistant models and skills |

Agents cite these identifiers on proposals. They do not claim that citing the standard completes compliance.
