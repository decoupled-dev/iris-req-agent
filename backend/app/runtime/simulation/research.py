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
