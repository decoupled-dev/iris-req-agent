import { useMemo, useState } from "react";
import { Search } from "lucide-react";
import { api } from "../api";
import { usePoll } from "../hooks";
import { Chip, PageHeader, Segmented } from "../components/ui";

type View = "signals" | "triggers";

const KIND_LABEL: Record<string, string> = { utterance: "Utterance", vehicle_event: "Vehicle event", derived: "Derived" };

export default function Signals() {
  const { data: cat } = usePoll(api.signals, 6000);
  const [view, setView] = useState<View>("signals");
  const [domain, setDomain] = useState("all");
  const [q, setQ] = useState("");

  const signals = useMemo(() => (cat?.signals ?? []).filter((s) =>
    (domain === "all" || s.domain === domain)
    && `${s.alias} ${s.label} ${s.vss} ${s.vhal}`.toLowerCase().includes(q.toLowerCase())), [cat, domain, q]);
  if (!cat) return null;

  const used = cat.signals.filter((s) => s.used_by.length).length;
  const actuators = cat.signals.filter((s) => s.access === "actuator").length;
  const triggersUsed = cat.triggers.filter((t) => t.used_by.length).length;

  return (
    <>
      <PageHeader title="Vehicle signals"
        subtitle={<>What the companion can sense and act on. {cat.source} · {cat.version} · <span className="ref-note">{cat.status}</span></>} />
      <div className="kpis kpis-4">
        <div className="stat"><div className="stat-label">Signals</div><div className="stat-value">{cat.signals.length}</div><div className="stat-sub">{cat.domains.length} domains</div></div>
        <div className="stat"><div className="stat-label">Actuators</div><div className="stat-value">{actuators}</div>
          <div className="stat-sub">{cat.signals.filter((s) => s.tier === "high-impact").length} high-impact · {cat.signals.filter((s) => s.tier === "prohibited").length} prohibited</div></div>
        <div className="stat"><div className="stat-label">Used by requirements</div><div className="stat-value">{used}</div><div className="stat-sub">of {cat.signals.length} signals</div></div>
        <div className="stat"><div className="stat-label">Triggers covered</div><div className="stat-value">{triggersUsed}<span className="stat-of"> / {cat.triggers.length}</span></div><div className="stat-sub">with at least one behaviour</div></div>
      </div>

      <div className="card">
        <div className="toolbar">
          <Segmented<View> value={view} onChange={setView} options={[
            { value: "signals", label: "Signals", count: cat.signals.length },
            { value: "triggers", label: "Triggers", count: cat.triggers.length },
          ]} />
          {view === "signals" && (
            <>
              <div className="search"><Search size={14} /><input placeholder="Search alias, label, VSS, VHAL" value={q} onChange={(e) => setQ(e.target.value)} /></div>
              <select value={domain} onChange={(e) => setDomain(e.target.value)}>
                <option value="all">All domains</option>
                {cat.domains.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
              </select>
              <span className="toolbar-count">{signals.length} signals</span>
            </>
          )}
        </div>
        <div className="table-wrap">
          {view === "signals" ? (
            <table className="table table-static">
              <thead>
                <tr><th>Signal</th><th>VSS path</th><th>VHAL</th><th>Type</th><th>Access</th><th>Flags</th><th>Used by</th></tr>
              </thead>
              <tbody>
                {signals.map((s) => (
                  <tr key={s.alias}>
                    <td><code className="sig-alias">{s.alias}</code><div className="sub">{s.label}</div></td>
                    <td className="mono muted vss">{s.vss}</td>
                    <td className="mono muted">{s.vhal}</td>
                    <td className="nowrap">{s.type}{s.unit && <span className="muted"> · {s.unit}</span>}
                      {s.enum && <div className="sub">{s.enum.join(" | ")}</div>}
                      {s.range && <div className="sub">{s.range[0]} … {s.range[1]}</div>}</td>
                    <td>{s.access === "actuator"
                      ? <span className={`tier tier-${s.tier}`}>{s.tier}</span>
                      : <span className="muted">read</span>}</td>
                    <td>
                      {s.availability === "optional" && <Chip tone="warning">optional</Chip>}
                      {s.privacy && <Chip tone="info">{s.privacy}</Chip>}
                    </td>
                    <td className="used-by"><UsedBy refs={s.used_by} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <table className="table table-static">
              <thead><tr><th>Trigger</th><th>Kind</th><th>Description</th><th>Source</th><th>Used by</th></tr></thead>
              <tbody>
                {cat.triggers.map((t) => (
                  <tr key={t.id}>
                    <td><span className={`trigger trigger-${t.kind}`}>{t.id}</span></td>
                    <td className="nowrap">{KIND_LABEL[t.kind]}{t.stationary && <span className="muted"> · stationary</span>}</td>
                    <td>{t.label}</td>
                    <td className="mono muted">{t.source}</td>
                    <td className="used-by">{t.used_by.length ? <UsedBy refs={t.used_by} /> : <span className="tier tier-prohibited">uncovered</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      <div className="card responses">
        <h3>Response types</h3>
        <p className="muted">The THEN vocabulary. Every behavioural requirement's responses use one of these.</p>
        <div className="resp-grid">
          {cat.responses.map((r) => (
            <div key={r.type}><span className={`resp resp-${r.type.toLowerCase()}`}>{r.label}</span><p>{r.rule}</p></div>
          ))}
        </div>
      </div>
    </>
  );
}

/** Requirement IDs in the register, plus a count of proposals still in the inbox. */
function UsedBy({ refs }: { refs: string[] }) {
  if (!refs.length) return <span className="muted">—</span>;
  const ids = refs.filter((r) => !r.startsWith("inbox: "));
  const proposed = refs.length - ids.length;
  return (
    <span title={refs.map((r) => r.replace("inbox: ", "proposed: ")).join("\n")}>
      {ids.slice(0, 3).join(", ")}
      {ids.length > 3 && <span className="muted"> +{ids.length - 3}</span>}
      {proposed > 0 && <span className="proposed">{proposed} proposed</span>}
    </span>
  );
}
