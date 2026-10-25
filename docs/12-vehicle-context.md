# Vehicle context

The companion is only as situated as the signals it can read and the actions it may take. This document defines the **vehicle signal catalog** the companion uses, the **triggers** it reacts to, the **responses** it may give, and how behavioural requirements are written as **GIVEN / WHEN / THEN** scenarios.

The machine-readable sources are `backend/app/knowledge/packs/vehicle_signals.yaml` (catalog) and `vehicle_scenarios.yaml` (scenarios). The Vehicle signals page in the workbench shows both, with the requirements that use each signal.

## Signal catalog

**Status: reference.** The catalog uses COVESA Vehicle Signal Specification (VSS) paths, with an indicative Android Automotive VHAL property where one exists. Paths starting `OEM.` are OEM extensions where VSS has no node. The program replaces this catalog with the OEM signal database; the runtime choice (AAOS or QNX) stays open.

Each signal records:

| Attribute | Meaning |
| --- | --- |
| `alias` | Name used in scenarios, e.g. `cabin_temp` |
| `vss`, `vhal` | Catalog path and indicative AAOS property |
| `type`, `unit`, `range` / `enum` | Value domain |
| `access` | `read`, or `actuator` if the companion may request a change |
| `tier` | For actuators: `comfort`, `high-impact`, or `prohibited` (action tiers in [09-cognitive-companion.md](09-cognitive-companion.md)) |
| `family`, `zone` | Groups per-zone signals so a scenario can target "the speaker's zone" |
| `availability` | `optional` for fitment-dependent signals (driver monitoring, fog sensor, rear radar) |
| `privacy` | `personal` or `biometric` where the privacy agent must review use |

### Domains and representative signals

| Domain | Signals (76 in total) | Actuators |
| --- | --- | --- |
| Vehicle state | `ignition_state`, `gear`, `vehicle_speed`, `odometer`, `trip_duration` | — |
| Energy and charging | `battery_soc`, `range_remaining`, `range_margin_at_destination`, `charging_active`, `charge_cable_connected` | — |
| Body and closures | `door_open_*` ×4, `trunk_open`, `window_pos_*` ×4, `any_window_open`, `sunroof_pos`, `doors_locked`, `child_lock` | Windows, sunroof, locks, child lock: **high-impact** |
| Climate | `cabin_temp`, `setpoint_*` ×3, `outside_temp`, `cabin_humidity`, `sun_load`, `ac_on`, `fan_speed`, `recirculation`, `front_defrost`, `windshield_fog`, `seat_climate_*` ×4, `steering_heat` | Setpoints, AC, fan, recirculation, defrost, seat and steering heat: **comfort** |
| Occupants and driver state | `seat_occupied_*` ×4, `rear_occupant_detected`, `seatbelt_*` ×4, `speaker_seat`, `speaker_confidence`, `driver_drowsiness`, `driver_distraction`, `active_profile`, `affect_awareness_enabled` | — |
| Driving context | `driver_workload` (COG-03), `turn_signal`, `nav_guidance_active`, `next_manoeuvre_distance`, `nav_destination_set`, `nav_eta`, `adas_cruise_active`, `adas_lane_keep_active` | Driver assistance: **prohibited** |
| Environment | `rain_intensity`, `ambient_light`, `location`, `local_time`, `rain_forecast_probability` | — |
| Connectivity, media and personal | `network_available`, `phone_connected`, `call_state`, `media_state`, `media_volume`, `calendar_next_event`, `memory_climate_preference`, `ecall_state` | Volume: comfort; eCall: **high-impact** |

## Triggers

A scenario reacts to exactly one trigger.

| Kind | Triggers |
| --- | --- |
| Utterance | `UTTERANCE`, with an intent such as `thermal_discomfort.cold` and an example phrase |
| Vehicle event | `IGN_ON`, `IGN_OFF`, `DOOR_OPEN`, `DOOR_CLOSE`, `SEAT_OCCUPIED`, `GEAR_PARK`, `CHARGING_STARTED`, `RAIN_DETECTED`, `INCOMING_CALL`, `DESTINATION_REACHED` |
| Derived | `THERMAL_DEVIATION_SUSTAINED`, `LOW_RANGE`, `WINDSHIELD_FOG`, `DROWSINESS_DETECTED`, `LONG_DRIVE`, `CALENDAR_DEPARTURE` |

Triggers marked *stationary* in the catalog (ignition, doors, seat, park, charging) imply the vehicle is not moving.

## Responses

| Type | Rule |
| --- | --- |
| `ACT` | Execute a comfort-tier action and say what was done; undoable by voice |
| `CONFIRM_THEN_ACT` | Ask yes/no and act only on explicit confirmation; **required** for high-impact actuators |
| `ASK` | Clarify who or what before doing anything |
| `SUGGEST` | Offer an action and name the signal that triggered it; dismissible |
| `INFORM` | State a fact grounded in a signal |
| `DEFER` | Hold non-urgent speech until driver workload is low |
| `REFUSE` | Decline a prohibited function and explain |

A response may carry `target` and `value` (an actuator alias or family, with `zone`: a zone, `speaker`, or `all`) and `say` (the spoken text, with `{placeholders}` for runtime values).

## Writing behavioural requirements

A requirement that describes how the companion reacts to the vehicle, the cabin, or an occupant has:

1. a one-line **`shall` statement**: what suppliers contract against, and what the register, Word, and Excel list
2. a structured **`scenario`** next to it: GIVEN conditions, WHEN one trigger, THEN responses

Rules, enforced by `check_scenarios` and by the compliance gate:

| Rule | Severity if broken |
| --- | --- |
| GIVEN uses only catalog signals and valid enum values | major |
| WHEN names one catalog trigger; `UTTERANCE` names an intent | major |
| ACT, CONFIRM_THEN_ACT, and SUGGEST target actuators only | major |
| High-impact actuators use CONFIRM_THEN_ACT | **critical** |
| Prohibited functions are only REFUSEd | **critical** |
| Proactive speech (SUGGEST or INFORM on a system trigger) while the vehicle may be moving has a `driver_workload` condition or a DEFER | major |
| Optional-fitment signals carry a note on fallback or applicability | minor |
| A behavioural requirement for COG-01, 02, 12, 13, or 14 carries a scenario | minor |
| Every catalog trigger has at least one behaviour | minor |

Branches become separate scenarios, so each row is one test case. Non-behavioural requirements (data retention, update integrity, latency, persona style guide) have no scenario.

## Worked examples

**Cold occupant, known seat** (`SYS-COG`, COG-01/02/04)

> The voice assistant shall respond to a cold-discomfort utterance by raising the climate setpoint of the speaker's zone by 2 °C and stating the change.

- **GIVEN** `ignition_state` = ON AND `speaker_seat` ≠ unknown AND `speaker_confidence` ≥ 0.8 AND `cabin_temp` < `setpoint_driver`
- **WHEN** UTTERANCE `thermal_discomfort.cold`: "I'm freezing"
- **THEN** ACT `climate_setpoint` [speaker zone] → +2 °C: "Warming your side up to {new_setpoint} degrees."

**Same discomfort, unknown speaker** (COG-01/06)

- **GIVEN** `ignition_state` = ON AND `speaker_confidence` < 0.8 AND `seat_occupied_passenger`
- **WHEN** UTTERANCE `thermal_discomfort.hot`: "I'm too warm"
- **THEN** ASK: "Is that for you in the driver's seat or the passenger seat?"

**Hot occupant with window open** (COG-02/10/14)

- **GIVEN** `ignition_state` = ON AND `speaker_seat` = driver AND `window_pos_driver` > 10 % AND NOT `ac_on` AND `outside_temp` > 25 °C
- **WHEN** UTTERANCE `thermal_discomfort.hot`: "It's boiling in here"
- **THEN** CONFIRM_THEN_ACT `window_pos_driver` → 0 %: "Your window's open. Shall I close it and switch on the air conditioning?"; THEN ACT `ac_on` → true

**Ignition on with a known profile** (COG-08/15)

- **GIVEN** `seat_occupied_driver` AND `active_profile` known AND `memory_climate_preference` known
- **WHEN** IGN_ON
- **THEN** ACT `setpoint_driver` → `memory_climate_preference`; INFORM: "Morning, {profile_name}. I've set it to your usual {memory_climate_preference} degrees."

**Driver leaves with ignition on** (COG-02)

- **GIVEN** `ignition_state` = ON AND `gear` = P AND NOT `seat_occupied_driver`
- **WHEN** DOOR_OPEN (driver door)
- **THEN** INFORM: "The car is still switched on."

**Occupant left in the rear** (`SYS-SAFE`, preliminary ASIL A, to be confirmed by the safety manager)

- **GIVEN** `gear` = P AND `rear_occupant_detected` (optional fitment; falls back to rear seat occupancy)
- **WHEN** IGN_OFF
- **THEN** INFORM: "Please check the back seat before you leave."

The scenario pack holds 23 vehicle-context scenarios across climate, entry and exit, driving, and arrival. A further 13 scenarios sit on the behavioural requirements of the capability, production-assistant, distraction, and safety packs.

## How the pipeline uses this

- The **vehicle context** agent (research stage) reads the catalog and the scenario pack, validates every draft with `check_scenarios`, and proposes behavioural requirements with their scenarios. It flags every optional-fitment dependency as a finding for variant planning.
- **Synthesis** keeps scenarios unchanged when merging.
- The **compliance gate** validates every included scenario and reports trigger coverage.
- **Export** prints each scenario under its requirement in Word, adds a Vehicle context section, and adds the Scenarios and Vehicle signals sheets to Excel ([06-export.md](06-export.md)).
