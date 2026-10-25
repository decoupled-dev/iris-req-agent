import { useEffect, useMemo, useState } from "react";
import { FileText, Search } from "lucide-react";
import { api, Requirement } from "../api";
import { usePoll } from "../hooks";
import { relative } from "../format";
import { CategoryTag, Chip, Drawer, Empty, Field, PageHeader, StateBadge } from "../components/ui";

const CATEGORIES = ["STK", "SYS-FUNC", "SYS-PERF", "SYS-HMI", "SYS-COG", "SYS-SAFE", "SYS-SEC", "SYS-PRIV", "SYS-DIST"];
const STATES = ["Draft", "In Review", "Baselined"];

export default function Requirements() {
  const reqs = usePoll(api.requirements, 5000);
  const [q, setQ] = useState("");
  const [cat, setCat] = useState("");
  const [state, setState] = useState("");
  const [open, setOpen] = useState<Requirement | null>(null);

  const rows = useMemo(() => (reqs.data ?? []).filter((r) =>
    r.state !== "Superseded" && (!cat || r.category === cat) && (!state || r.state === state)
    && `${r.id} ${r.title} ${r.statement} ${r.cognitive_capability.join(" ")}`.toLowerCase().includes(q.toLowerCase())),
  [reqs.data, q, cat, state]);

  return (
    <>
      <PageHeader title="Requirements" subtitle="The register is the system of record. Agents never overwrite baselined text." />
      <div className="card">
        <div className="toolbar">
          <div className="search"><Search size={14} /><input placeholder="Search ID, title, statement, COG-xx" value={q} onChange={(e) => setQ(e.target.value)} /></div>
          <select value={cat} onChange={(e) => setCat(e.target.value)}>
            <option value="">All categories</option>
            {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
          </select>
          <select value={state} onChange={(e) => setState(e.target.value)}>
            <option value="">All states</option>
            {STATES.map((s) => <option key={s}>{s}</option>)}
          </select>
          <span className="toolbar-count">{rows.length} items</span>
        </div>
        {rows.length === 0 ? (
          <Empty icon={<FileText size={22} />} title="No requirements">Accept proposals in Review to populate the register.</Empty>
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr><th>ID</th><th>Title</th><th>Category</th><th>State</th><th>Priority</th><th>Capability</th><th className="num">Ver.</th><th>Updated</th></tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.id} onClick={() => setOpen(r)}>
                    <td className="mono">{r.id}</td>
                    <td className="title-cell"><div>{r.title}</div><div className="sub">{r.statement}</div></td>
                    <td><CategoryTag category={r.category} /></td>
                    <td><StateBadge state={r.state} /></td>
                    <td>{r.priority}</td>
                    <td>{r.cognitive_capability.map((c) => <Chip key={c} tone="accent">{c}</Chip>)}</td>
                    <td className="num">{r.version}</td>
                    <td className="muted nowrap">{relative(r.updated_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      <Drawer open={!!open} onClose={() => setOpen(null)} title={open && <><span className="mono">{open.id}</span> {open.title}</>}>
        {open && <RequirementDetail req={open} />}
      </Drawer>
    </>
  );
}

function RequirementDetail({ req }: { req: Requirement }) {
  const [history, setHistory] = useState<Requirement[]>([]);
  useEffect(() => void api.history(req.id).then(setHistory), [req.id]);
  return (
    <div className="detail">
      <div className="rd-tags"><CategoryTag category={req.category} /><StateBadge state={req.state} /><Chip>{req.priority}</Chip><Chip>v{req.version}</Chip></div>
      <p className="detail-statement">{req.statement}</p>
      <Field label="Rationale">{req.rationale}</Field>
      <Field label="Acceptance criteria">{req.acceptance_criteria || "—"}</Field>
      <Field label="Verification method">{req.verification_method || "—"}</Field>
      <Field label="Source">{req.source}</Field>
      <Field label="Cognitive capability">{req.cognitive_capability.join(", ") || "—"}</Field>
      <Field label="Standard references">{req.standard_references.join(", ") || "—"}</Field>
      {req.preliminary_asil && <Field label="Preliminary ASIL">{req.preliminary_asil} — {req.asil_note}</Field>}
      <div className="field-label" style={{ marginTop: 20 }}>Version history</div>
      <ol className="history">
        {[...history].reverse().map((h) => (
          <li key={h.version}>
            <div className="history-head"><b>v{h.version}</b><StateBadge state={h.state} /><span className="muted">{relative(h.updated_at)} · {h.updated_by}</span></div>
            <div className="muted">{h.change_note}</div>
          </li>
        ))}
      </ol>
    </div>
  );
}
