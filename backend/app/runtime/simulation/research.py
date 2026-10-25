"""Research-stage policies: three pack readers and companion cognition."""

from __future__ import annotations

from . import call, finding_id, norm, policy, result, turn

PACKS = {
    "google_assistant_reference": ("google_assistant_reference", "Google's driving-mode assistant"),
    "oem_feature_research": ("production_assistants", "production OEM assistants"),
    "customer_expectations": ("customer_themes", "owner-reported customer themes"),
}


@policy(*PACKS)
def pack_research(req):
    pack, subject = PACKS[req.agent_id]
    kb = result(req, "search_knowledge", pack=pack)
    if kb is None:
        return turn(f"I'm asked to turn {subject} into findings and candidate requirements. I'll start by reading "
                    f"the `{pack}` knowledge pack so every finding is grounded in a versioned source.",
                    [call(req, "search_knowledge", pack=pack)])
    reg = result(req, "list_requirements")
    entries = kb["entries"]
    if reg is None:
        with_prop = sum(1 for e in entries if e.get("proposal"))
        return turn(f"The pack (version {kb['version']}) has {len(entries)} entries; {with_prop} of them justify a "
                    f"requirement. Before drafting, I'll check the register so I can flag behaviour that is already "
                    f"specified instead of proposing it as new.", [call(req, "list_requirements")])

    existing = {norm(r["title"]) for r in reg["requirements"]}
    source = f"{kb['source']} ({kb['version']})"
    findings, proposals, skipped = [], [], []
    for e in entries:
        fid = finding_id(e["key"])
        findings.append({"id": fid, "title": e["title"], "statement": e["finding"], "source": source,
                         "confidence": "high"})
        if spec := e.get("proposal"):
            title = spec.get("title", e["title"])
            if norm(title) in existing:
                skipped.append(title)
                continue
            proposals.append({"title": title, **spec, "source": fid,
                              "change_note": f"Initial proposal from {req.agent_id}"})
    no_prop = [e["title"] for e in entries if not e.get("proposal")]
    thinking = (f"Mapping each entry to a finding. {len(proposals)} entries become candidate requirements"
                + (f"; {len(skipped)} are already in the register ({', '.join(skipped)})" if skipped else "")
                + (f". {', '.join(no_prop)} stay findings only: they inform positioning but don't yet justify a "
                   f"`shall` statement" if no_prop else "") + ". Submitting.")
    summary = (f"Reviewed {len(entries)} {subject} entries from pack {kb['version']}: {len(findings)} findings, "
               f"{len(proposals)} candidate requirements for synthesis"
               + (f", {len(skipped)} already specified." if skipped else "."))
    return turn(thinking, [call(req, "submit_result", summary=summary, findings=findings, proposals=proposals)])


@policy("companion_cognition")
def companion(req):
    cat = result(req, "get_capability_catalog")
    cov = result(req, "get_cognitive_coverage")
    if cat is None or cov is None:
        return turn("My job is to close the gap between the register and the target cognitive level. I need two "
                    "things at once: the capability catalog up to the target, and current coverage.",
                    [call(req, "get_capability_catalog"), call(req, "get_cognitive_coverage")])

    covered = {row["id"]: row for row in cov["capabilities"]}
    findings, proposals = [], []
    by_level: dict[str, int] = {}
    for cap in cat["capabilities"]:
        row = covered[cap["id"]]
        fid = f"find_cog_{cap['id'][-2:]}"
        status = f"covered by {', '.join(row['requirement_ids'])}" if row["covered"] else "not covered"
        findings.append({"id": fid, "title": f"{cap['id']} {cap['title']}",
                         "statement": f"{cap['faculty']} capability at {cap['level']}; {status}.",
                         "source": f"{cat['source']} ({cat['version']})", "confidence": "high"})
        if row["covered"]:
            continue
        spec = cap["proposal"]
        cl5 = cap["level"] == "CL5"
        rationale = spec["rationale"] + (" Depends on companion principles: honest identity, no manipulation, "
                                         "affect is opt-in." if cl5 else "")
        proposals.append({
            "category": spec.get("category", "SYS-COG"), "title": cap["title"],
            "priority": "Should" if cl5 else "Must", **spec, "rationale": rationale,
            "cognitive_capability": sorted({cap["id"], *spec.get("cognitive_capability", [])}),
            "source": fid, "change_note": f"Initial proposal for {cap['id']} ({cap['level']})"})
        by_level[cap["level"]] = by_level.get(cap["level"], 0) + 1

    gaps = ", ".join(f"{n} at {lvl}" for lvl, n in sorted(by_level.items())) or "none"
    thinking = (f"Target is {cat['target_level']}; the register specifies {cov['specified_level']}. "
                f"Uncovered capabilities: {gaps}. CL0–CL4 gaps are proposed as Must. CL5 items go in as Should and "
                f"name the companion principles they rely on, because privacy and AI-regulation review must close "
                f"them before baseline. COG-13 is drafted as SYS-DIST so the gate's proactive-timing pairing holds.")
    summary = (f"Target {cat['target_level']}, register specifies {cov['specified_level']}. "
               f"{len(proposals)} of {len(findings)} capabilities need a requirement ({gaps}).")
    return turn(thinking, [call(req, "submit_result", summary=summary, findings=findings, proposals=proposals,
                                metrics={"specified_before": cov["specified_level"], "gaps": len(proposals)})])


@policy("vehicle_context")
def vehicle_context(req):
    cat = result(req, "get_vehicle_signals")
    kb = result(req, "search_knowledge", pack="vehicle_scenarios")
    if cat is None or kb is None:
        return turn("I specify how the companion reacts to the vehicle: GIVEN conditions on catalog signals, WHEN one "
                    "trigger or utterance, THEN a response that respects the action tiers. I need the signal catalog "
                    "and the scenario pack.",
                    [call(req, "get_vehicle_signals"), call(req, "search_knowledge", pack="vehicle_scenarios")])

    drafts = [{"title": e["proposal"]["title"], "scenario": e["proposal"]["scenario"]} for e in kb["entries"]]
    checked, reg = result(req, "check_scenarios"), result(req, "list_requirements")
    if checked is None or reg is None:
        actuators = [s for s in cat["signals"] if s["access"] == "actuator"]
        high = sum(1 for s in actuators if s.get("tier") == "high-impact")
        optional = sum(1 for s in cat["signals"] if s.get("availability") == "optional")
        return turn(f"The catalog ({cat['status']}) has {len(cat['signals'])} signals, {len(actuators)} of them "
                    f"actuators ({high} high-impact), {optional} optional fitments, and {len(cat['triggers'])} triggers. "
                    f"I've drafted {len(drafts)} scenarios from the pack. Before submitting I'll validate every one "
                    f"against the catalog and tiers, and check the register for behaviour already specified.",
                    [call(req, "check_scenarios", scenarios=drafts), call(req, "list_requirements")])

    existing = {norm(r["title"]) for r in reg["requirements"]}
    signals = {s["alias"]: s for s in cat["signals"]}
    source = f"{kb['source']} ({kb['version']})"
    invalid = {r["index"] for r in checked["results"] if not r["valid"]}
    findings, proposals, skipped = [], [], 0
    for i, e in enumerate(kb["entries"]):
        fid = finding_id(e["key"])
        findings.append({"id": fid, "title": e["title"], "statement": e["finding"], "source": source,
                         "confidence": "high"})
        spec = e["proposal"]
        if i in invalid:
            continue
        if norm(spec["title"]) in existing:
            skipped += 1
            continue
        p = {**spec, "source": fid, "change_note": f"Initial proposal from vehicle_context ({e['key']})"}
        if p["category"] == "SYS-SAFE":
            p["asil_note"] = "to be confirmed by the safety manager"
        proposals.append(p)

    used = {c["signal"] for e in kb["entries"] for c in e["proposal"]["scenario"]["given"]}
    optional = sorted(a for a in used if signals.get(a, {}).get("availability") == "optional")
    for alias in optional:
        findings.append({"id": f"find_fit_{alias}", "title": f"Optional fitment: {alias}",
                         "statement": f"Scenarios rely on '{signals[alias]['label']}' ({signals[alias]['vss']}), "
                                      f"which is optional fitment; variants without it need the stated fallback.",
                         "source": f"{cat['source']} ({cat['version']})", "confidence": "high"})
    triggers = {e["proposal"]["scenario"]["when"]["trigger"] for e in kb["entries"]}
    thinking = (f"{checked['valid']} of {checked['checked']} scenarios pass validation"
                + (f"; {len(invalid)} dropped until fixed" if invalid else "")
                + f". They use {len(used)} distinct signals and {len(triggers)} of {len(cat['triggers'])} triggers. "
                  f"{len(optional)} optional-fitment dependencies ({', '.join(optional) or 'none'}) become findings so "
                  f"variant planning sees them. Each proposal keeps a one-line shall statement with its scenario"
                + (f"; {skipped} already in the register" if skipped else "") + ".")
    summary = (f"{len(proposals)} GIVEN/WHEN/THEN requirements from {len(kb['entries'])} vehicle-context scenarios, all "
               f"validated against {len(cat['signals'])} catalog signals; {len(optional)} optional-fitment dependencies "
               f"flagged.")
    return turn(thinking, [call(req, "submit_result", summary=summary, findings=findings, proposals=proposals,
                                metrics={"scenarios": len(proposals), "signals_used": len(used),
                                         "triggers_covered": len(triggers)})])
