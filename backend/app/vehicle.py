"""Vehicle signal catalog, scenario validation, and GIVEN/WHEN/THEN rendering. See docs/12-vehicle-context.md."""

from __future__ import annotations

from functools import cache
from typing import Any

from .knowledge import load_pack
from .models import Proposal, Requirement, Scenario

OPS = {"==", "!=", "<", ">", "<=", ">=", "in", "known"}
OP_TEXT = {"==": "is", "!=": "is not", "<": "<", ">": ">", "<=": "≤", ">=": "≥", "in": "is one of"}
RESPONSE_TYPES = ("ACT", "CONFIRM_THEN_ACT", "ASK", "SUGGEST", "INFORM", "DEFER", "REFUSE")
SPOKEN_PROACTIVE = {"SUGGEST", "INFORM"}
# Capabilities whose requirements describe a reaction to vehicle state, so they should carry a scenario.
REACTIVE_CAPS = {"COG-01", "COG-02", "COG-12", "COG-13", "COG-14"}


@cache
def catalog() -> dict:
    return load_pack("vehicle_signals")


@cache
def signals() -> dict[str, dict]:
    return {s["alias"]: s for s in catalog()["signals"]}


@cache
def families() -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for s in catalog()["signals"]:
        if fam := s.get("family"):
            out.setdefault(fam, []).append(s)
    return out


@cache
def triggers() -> dict[str, dict]:
    return {t["id"]: t for t in catalog()["triggers"]}


def resolve(name: str) -> list[dict]:
    """A signal alias or a family name -> the signals it denotes."""
    if name in signals():
        return [signals()[name]]
    return families().get(name, [])


def _ref(value: Any) -> str | None:
    return value[1:] if isinstance(value, str) and value.startswith("@") else None


def validate(scenario: Scenario | dict) -> list[dict]:
    """Rule check for one scenario. Each issue: {check, severity, detail}."""
    sc = scenario if isinstance(scenario, Scenario) else Scenario.model_validate(scenario)
    issues: list[dict] = []

    def issue(check: str, severity: str, detail: str):
        issues.append({"check": check, "severity": severity, "detail": detail})

    for c in sc.given:
        found = resolve(c.signal)
        if not found:
            issue("unknown-signal", "major", f"GIVEN uses unknown signal '{c.signal}'")
            continue
        if c.op not in OPS:
            issue("operator", "major", f"GIVEN '{c.signal}' uses unknown operator '{c.op}'")
        if (ref := _ref(c.value)) and not resolve(ref):
            issue("unknown-signal", "major", f"GIVEN '{c.signal}' compares with unknown signal '{ref}'")
        enum = found[0].get("enum")
        if enum and c.op in ("==", "!=", "in") and not _ref(c.value):
            values = c.value if isinstance(c.value, list) else [c.value]
            if bad := [v for v in values if v not in enum]:
                issue("enum-value", "major", f"'{c.signal}' has no value {bad}; allowed {enum}")
        if any(s.get("availability") == "optional" for s in found) and not c.note:
            issue("optional-fitment", "minor", f"'{c.signal}' is optional fitment; note the fallback or applicability")

    trig = triggers().get(sc.when.trigger)
    if trig is None:
        issue("unknown-trigger", "major", f"WHEN uses unknown trigger '{sc.when.trigger}'")
    elif trig["kind"] == "utterance" and not sc.when.intent:
        issue("intent", "major", "An UTTERANCE trigger needs an intent")

    if not sc.then:
        issue("empty-then", "major", "THEN has no response")
    for r in sc.then:
        if r.type not in RESPONSE_TYPES:
            issue("response-type", "major", f"Unknown response type '{r.type}'")
            continue
        if not r.target:
            if r.type in ("ACT", "CONFIRM_THEN_ACT"):
                issue("target", "major", f"{r.type} needs an actuator target")
            continue
        targets = resolve(r.target)
        if not targets:
            issue("unknown-signal", "major", f"THEN targets unknown signal '{r.target}'")
            continue
        if r.type in ("ACT", "CONFIRM_THEN_ACT", "SUGGEST") and any(t["access"] != "actuator" for t in targets):
            issue("not-writable", "major", f"'{r.target}' is read-only and cannot be acted on")
        tiers = {t.get("tier") for t in targets}
        if "prohibited" in tiers and r.type != "REFUSE":
            issue("prohibited", "critical", f"'{r.target}' is prohibited by voice; THEN must REFUSE")
        elif "high-impact" in tiers and r.type == "ACT":
            issue("high-impact", "critical", f"'{r.target}' is high-impact; use CONFIRM_THEN_ACT")

    stationary = bool(trig and trig.get("stationary"))
    stationary |= any(c.signal == "vehicle_speed" and c.op == "==" and c.value == 0 for c in sc.given)
    stationary |= any(c.signal == "gear" and c.op == "==" and c.value == "P" for c in sc.given)
    workload = any(c.signal == "driver_workload" for c in sc.given)
    proactive = trig is not None and trig["kind"] != "utterance"
    if proactive and not stationary and not workload and any(r.type in SPOKEN_PROACTIVE for r in sc.then):
        issue("workload", "major", "Proactive speech while the vehicle may be moving needs a driver_workload condition or DEFER")
    return issues


def _label(name: str) -> str:
    found = resolve(name)
    if name in signals():
        return found[0]["label"]
    return found[0]["label"].split(" ", 1)[-1] if found else name


def _value(name: str, value: Any) -> str:
    if (ref := _ref(value)) is not None:
        return _label(ref)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    unit = (resolve(name)[0].get("unit") if resolve(name) else None) or ""
    text = str(value)
    return f"{text} {unit}".strip() if unit and isinstance(value, (int, float)) else text


def _condition(c) -> str:
    label = _label(c.signal)
    if c.op == "known":
        return f"{label} is known"
    if isinstance(c.value, bool) and c.op in ("==", "!="):
        return label if c.value == (c.op == "==") else f"NOT {label}"
    return f"{label} {OP_TEXT.get(c.op, c.op)} {_value(c.signal, c.value)}"


def render_parts(scenario: Scenario | dict) -> dict[str, str]:
    sc = scenario if isinstance(scenario, Scenario) else Scenario.model_validate(scenario)
    given = [_condition(c) for c in sc.given]
    trig = triggers().get(sc.when.trigger, {"label": sc.when.trigger})
    when = (f"the occupant says “{sc.when.example}” (intent {sc.when.intent})" if sc.when.trigger == "UTTERANCE"
            else trig["label"] + (f" ({sc.when.example})" if sc.when.example else ""))
    then = []
    for r in sc.then:
        part = r.type.replace("_", " ")
        if r.target:
            zone = f" [{r.zone} zone]" if r.zone else ""
            val = f" → {_value(r.target, r.value)}" if r.value not in (None, "") else ""
            part += f" {_label(r.target)}{zone}{val}"
        if r.say:
            part += f": “{r.say}”"
        then.append(part)
    return {"given": " AND ".join(given) or "—", "when": when, "then": "; THEN ".join(then)}


def render(scenario: Scenario | dict) -> str:
    p = render_parts(scenario)
    return f"GIVEN {p['given']} WHEN {p['when']} THEN {p['then']}"


def signals_used(scenario: Scenario | None) -> list[str]:
    if scenario is None:
        return []
    names = [c.signal for c in scenario.given] + [r.target for r in scenario.then if r.target]
    names += [ref for c in scenario.given if (ref := _ref(c.value))]
    return list(dict.fromkeys(s["alias"] for n in names for s in resolve(n)))


def usage(requirements: list[Requirement], proposals: list[Proposal]) -> dict[str, dict[str, list[str]]]:
    """Which requirements (by ID) or proposals (by title) use each signal and trigger."""
    sig: dict[str, list[str]] = {}
    trig: dict[str, list[str]] = {}
    items = [(r.id, r.scenario) for r in requirements] + [(f"inbox: {p.title}", p.scenario) for p in proposals]
    for ref, sc in items:
        if sc is None:
            continue
        for alias in signals_used(sc):
            sig.setdefault(alias, []).append(ref)
        trig.setdefault(sc.when.trigger, []).append(ref)
    return {"signals": sig, "triggers": trig}
