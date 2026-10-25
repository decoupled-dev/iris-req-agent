import { useEffect, useState } from "react";
import { api, Condition, Scenario as ScenarioT, ScenarioResponse, Signal, SignalCatalog } from "../api";

// The catalog is static per session; fetch it once for labels, units and tooltips.
let catalogPromise: Promise<SignalCatalog> | null = null;
export function useCatalog() {
  const [cat, setCat] = useState<SignalCatalog | null>(null);
  useEffect(() => {
    catalogPromise ??= api.signals();
    catalogPromise.then(setCat).catch(() => (catalogPromise = null));
  }, []);
  return cat;
}

const OP: Record<string, string> = { "==": "=", "!=": "≠", "<": "<", ">": ">", "<=": "≤", ">=": "≥", in: "∈" };
const RESPONSE_LABEL: Record<ScenarioResponse["type"], string> = {
  ACT: "Act", CONFIRM_THEN_ACT: "Confirm → act", ASK: "Ask", SUGGEST: "Suggest", INFORM: "Inform", DEFER: "Defer", REFUSE: "Refuse",
};

function lookup(cat: SignalCatalog | null, name: string): Signal | undefined {
  return cat?.signals.find((s) => s.alias === name) ?? cat?.signals.find((s) => s.family === name);
}

function fmt(value: unknown, sig?: Signal): string {
  if (typeof value === "string" && value.startsWith("@")) return value.slice(1);
  if (typeof value === "boolean") return value ? "true" : "false";
  if (Array.isArray(value)) return value.join(" | ");
  if (typeof value === "number" && sig?.unit) return `${value} ${sig.unit}`;
  return String(value ?? "");
}

function tooltip(sig?: Signal) {
  if (!sig) return "Not in catalog";
  return [sig.label, sig.vss, sig.vhal !== "—" ? `VHAL ${sig.vhal}` : "", sig.tier ? `tier: ${sig.tier}` : "",
    sig.availability === "optional" ? "optional fitment" : ""].filter(Boolean).join("\n");
}

function ConditionChip({ c, cat }: { c: Condition; cat: SignalCatalog | null }) {
  const sig = lookup(cat, c.signal);
  return (
    <span className={`cond ${sig?.availability === "optional" ? "cond-optional" : ""}`} title={tooltip(sig) + (c.note ? `\n${c.note}` : "")}>
      <code className="cond-sig">{c.signal}</code>
      {c.op === "known" ? <span className="cond-op">known</span> : (
        <>
          <span className="cond-op">{OP[c.op] ?? c.op}</span>
          <span className="cond-val">{fmt(c.value, sig)}</span>
        </>
      )}
    </span>
  );
}

/** GIVEN / WHEN / THEN block for a behavioural requirement. */
export default function Scenario({ scenario, compact = false }: { scenario: ScenarioT; compact?: boolean }) {
  const cat = useCatalog();
  const trigger = cat?.triggers.find((t) => t.id === scenario.when.trigger);
  return (
    <div className={`gwt ${compact ? "gwt-compact" : ""}`}>
      <div className="gwt-row">
        <span className="gwt-kw">Given</span>
        <div className="gwt-body gwt-conds">
          {scenario.given.length ? scenario.given.map((c, i) => (
            <span key={i} className="cond-wrap">{i > 0 && <span className="gwt-and">and</span>}<ConditionChip c={c} cat={cat} /></span>
          )) : <span className="muted">No preconditions</span>}
        </div>
      </div>
      <div className="gwt-row">
        <span className="gwt-kw">When</span>
        <div className="gwt-body">
          <span className={`trigger trigger-${trigger?.kind ?? "utterance"}`} title={trigger?.label}>{scenario.when.trigger}</span>
          {scenario.when.intent && <code className="gwt-intent">{scenario.when.intent}</code>}
          {scenario.when.example && <span className="gwt-quote">“{scenario.when.example}”</span>}
          {!scenario.when.example && trigger && <span className="muted">{trigger.label}</span>}
        </div>
      </div>
      <div className="gwt-row">
        <span className="gwt-kw">Then</span>
        <ol className="gwt-body gwt-then">
          {scenario.then.map((r, i) => {
            const sig = r.target ? lookup(cat, r.target) : undefined;
            return (
              <li key={i}>
                <span className={`resp resp-${r.type.toLowerCase()}`}>{RESPONSE_LABEL[r.type] ?? r.type}</span>
                {r.target && (
                  <span className="resp-target" title={tooltip(sig)}>
                    <code>{r.target}</code>
                    {r.zone && <span className="muted"> · {r.zone} zone</span>}
                    {r.value !== undefined && r.value !== null && r.value !== "" && <> → <b>{fmt(r.value, sig)}</b></>}
                    {sig?.tier === "high-impact" && <span className="tier-flag">high-impact</span>}
                  </span>
                )}
                {r.say && <div className="gwt-say">“{r.say}”</div>}
                {r.note && <div className="gwt-note">{r.note}</div>}
              </li>
            );
          })}
        </ol>
      </div>
    </div>
  );
}
