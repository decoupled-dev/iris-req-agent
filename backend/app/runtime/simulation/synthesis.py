"""Synthesis policy: merge research candidates, respect the register."""

from __future__ import annotations

from . import call, norm, policy, result, turn

RESEARCH = ("google_assistant_reference", "oem_feature_research", "customer_expectations", "companion_cognition")


@policy("requirements_synthesis")
def synthesis(req):
    outputs = {a: result(req, "get_dependency_output", agent_id=a) for a in RESEARCH}
    if any(v is None for v in outputs.values()):
        return turn("I merge the four research outputs into one coherent set. Fetching all of them in parallel.",
                    [call(req, "get_dependency_output", agent_id=a) for a, v in outputs.items() if v is None])
    reg, inbox = result(req, "list_requirements"), result(req, "list_open_proposals")
    candidates = [p for o in outputs.values() for p in o["proposals"]]
    if reg is None or inbox is None:
        per = ", ".join(f"{len(o['proposals'])} from {a}" for a, o in outputs.items())
        return turn(f"{len(candidates)} candidates in total ({per}). Before merging I need the register, so updates "
                    f"reuse existing IDs and baselined text is left alone, and the inbox, so I don't re-propose "
                    f"what's already waiting for review.",
                    [call(req, "list_requirements"), call(req, "list_open_proposals")])

    merged: dict[str, dict] = {}
    for p in candidates:
        key = norm(p["title"])
        if key in merged:
            m = merged[key]
            m["source"] = ",".join(dict.fromkeys(m["source"].split(",") + p["source"].split(",")))
            m["cognitive_capability"] = sorted({*m.get("cognitive_capability", []), *p.get("cognitive_capability", [])})
            m["standard_references"] = list(dict.fromkeys(m.get("standard_references", []) + p.get("standard_references", [])))
        else:
            merged[key] = dict(p)
    existing = {norm(r["title"]): r for r in reg["requirements"]}
    waiting = {norm(p["title"]) for p in inbox["proposals"]}

    out, unchanged, updates, pending = [], 0, 0, 0
    for key, p in merged.items():
        if key in waiting:
            pending += 1
            continue
        if (r := existing.get(key)) is not None:
            if norm(r["statement"]) == norm(p["statement"]):
                unchanged += 1
                continue
            p = {**p, "id": r["id"], "change_note": f"Update of {r['id']} v{r['version']} from synthesis"}
            updates += 1
        else:
            p = {**p, "id": "", "change_note": "New requirement from synthesis"}
        out.append(p)
    dupes = len(candidates) - len(merged)
    thinking = (f"Merged by behaviour title: {dupes} duplicate{'s' if dupes != 1 else ''} folded, keeping every "
                f"source and capability ID on the surviving item. {unchanged} already match the register verbatim, "
                f"{pending} are already in the inbox, {updates} change an existing item and go in as new versions "
                f"under the same ID. Publishing {len(out)} to the inbox.")
    summary = (f"Merged {len(candidates)} research candidates into {len(merged)}. Published {len(out)} "
               f"({updates} updates); {unchanged} already in the register, {pending} already awaiting review.")
    return turn(thinking, [call(req, "submit_result", summary=summary, findings=[], proposals=out,
                                metrics={"candidates": len(candidates), "merged": len(merged), "updates": updates})])
