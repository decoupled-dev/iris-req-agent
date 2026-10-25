"""Compliance gate policy: run the rules, report findings and the specified level."""

from __future__ import annotations

from collections import Counter

from . import call, policy, result, turn


@policy("compliance_gate")
def gate(req):
    checks, cov = result(req, "run_compliance_checks"), result(req, "get_cognitive_coverage")
    if checks is None or cov is None:
        return turn("I gate the register before export. I'll run the deterministic checks and read cognitive "
                    "coverage in parallel, then report; I don't write requirements.",
                    [call(req, "run_compliance_checks"), call(req, "get_cognitive_coverage")])
    issues = checks["issues"]
    by_check = Counter(i["check"] for i in issues)
    by_sev = Counter(i["severity"] for i in issues)
    uncovered = [i["ref"] for i in issues if i["check"] == "coverage"]
    findings = [{"id": f"gate_{n:03d}", "title": i["title"], "statement": i["detail"],
                 "source": f"compliance_gate check: {i['check']}", "confidence": i["severity"]}
                for n, i in enumerate(issues, 1)]
    breakdown = ", ".join(f"{n} {c}" for c, n in by_check.most_common()) or "none"
    thinking = (f"{len(issues)} issues ({breakdown}). Specified level {cov['specified_level']} against target "
                f"{cov['target_level']}." + (f" {by_sev['critical']} critical issues block a supplier export."
                                             if by_sev["critical"] else "")
                + " Each issue becomes an open finding; coverage gaps name the capability so the companion agent "
                  "can close them on the next cycle.")
    summary = (f"Specified cognitive level {cov['specified_level']} of target {cov['target_level']}. "
               f"{len(findings)} open findings ({len(uncovered)} uncovered capabilities"
               + (f", {by_sev['critical']} critical" if by_sev["critical"] else "") + ").")
    return turn(thinking, [call(req, "submit_result", summary=summary, findings=findings, proposals=[], metrics={
        "specified_cognitive_level": cov["specified_level"], "target_cognitive_level": cov["target_level"],
        "uncovered": uncovered, "by_check": dict(by_check), "by_severity": dict(by_sev)})])
