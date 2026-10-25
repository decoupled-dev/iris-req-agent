"""Assurance policies: privacy, distraction, safety and cybersecurity."""

from __future__ import annotations

from . import call, finding_id, norm, policy, result, turn

PACKS = {
    "gdpr_privacy": ("privacy", "privacy"),
    "driver_distraction": ("distraction", "driver distraction"),
    "safety_cybersecurity": ("safety_security", "safety and cybersecurity"),
}


@policy(*PACKS)
def assurance(req):
    pack, label = PACKS[req.agent_id]
    synth = result(req, "get_dependency_output", agent_id="requirements_synthesis")
    kb = result(req, "search_knowledge", pack=pack)
    if synth is None or kb is None:
        return turn(f"I review the synthesised set from a {label} perspective and add constraints the research "
                    f"agents can't be expected to know. I need the synthesis output and the {label} pack.",
                    [call(req, "get_dependency_output", agent_id="requirements_synthesis"),
                     call(req, "search_knowledge", pack=pack)])
    reg, inbox = result(req, "list_requirements"), result(req, "list_open_proposals")
    if reg is None or inbox is None:
        review = set(kb.get("review_capabilities", []))
        hits = [p["title"] for p in synth["proposals"] if review & set(p.get("cognitive_capability", []))]
        note = (f" {len(hits)} synthesis items touch capabilities I must review ({', '.join(sorted(review))}): "
                f"{'; '.join(hits[:4])}{'…' if len(hits) > 4 else ''}." if hits else "")
        return turn(f"Synthesis published {len(synth['proposals'])} items; the pack has {len(kb['entries'])} "
                    f"{label} themes.{note} Checking the register and inbox so my proposals don't duplicate them.",
                    [call(req, "list_requirements"), call(req, "list_open_proposals")])

    seen = {norm(r["title"]) for r in reg["requirements"]} | {norm(p["title"]) for p in inbox["proposals"]}
    seen |= {norm(p["title"]) for p in synth["proposals"]}
    source = f"{kb['source']} ({kb['version']})"
    findings, proposals = [], []
    for e in kb["entries"]:
        fid = finding_id(e["key"])
        findings.append({"id": fid, "title": e["title"], "statement": e["finding"], "source": source,
                         "confidence": "high"})
        if (spec := e.get("proposal")) and norm(spec.get("title", e["title"])) not in seen:
            p = {"title": e["title"], **spec, "source": fid, "change_note": f"Initial proposal from {req.agent_id}"}
            if p["category"] == "SYS-SAFE":
                p["preliminary_asil"] = p.get("preliminary_asil") or "QM"
                p["asil_note"] = kb.get("asil_note", "to be confirmed by the safety manager")
            proposals.append(p)

    review = set(kb.get("review_capabilities", []))
    flagged = [p["title"] for p in synth["proposals"] if review & set(p.get("cognitive_capability", []))]
    flagged += [r["id"] for r in reg["requirements"] if review & set(r.get("cognitive_capability", []))]
    safe = [p for p in proposals if p["category"] == "SYS-SAFE"]
    extra = (f" Every SYS-SAFE item carries a preliminary ASIL marked '{kb.get('asil_note')}'; "
             f"{sum(1 for p in safe if p['preliminary_asil'] == 'B')} are class B candidates." if safe else "")
    thinking = (f"Each {label} theme becomes a finding; {len(proposals)} need a requirement that isn't already "
                f"covered.{extra} {len(flagged)} cognitive items go on my review list.")
    summary = (f"{len(proposals)} {label} proposals from {len(findings)} themes."
               + (f" {len(flagged)} cognitive items need {label} review." if flagged else ""))
    return turn(thinking, [call(req, "submit_result", summary=summary, findings=findings, proposals=proposals,
                                metrics={"review_items": flagged})])
