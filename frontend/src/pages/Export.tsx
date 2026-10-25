import { CheckCircle2, CircleAlert, Download, FileSpreadsheet, FileText } from "lucide-react";
import { api } from "../api";
import { usePoll } from "../hooks";
import { levelIndex } from "../format";
import { PageHeader } from "../components/ui";

export default function Export() {
  const { data: ov } = usePoll(api.overview, 3000);
  if (!ov) return null;
  const critical = ov.gate?.by_severity?.critical ?? 0;
  const inReview = (ov.by_state["Draft"] ?? 0) + (ov.by_state["In Review"] ?? 0);
  const checks = [
    { ok: !!ov.gate, label: "Compliance gate has run", detail: ov.gate ? `${ov.gate.findings} findings recorded as open points` : "Run the full cycle first" },
    { ok: critical === 0, label: "No critical gate findings", detail: `${critical} critical` },
    { ok: levelIndex(ov.specified_cognitive_level) >= levelIndex(ov.target_cognitive_level),
      label: `Cognitive level meets target ${ov.target_cognitive_level}`, detail: `Specified ${ov.specified_cognitive_level}` },
    { ok: ov.inbox === 0, label: "Review inbox is clear", detail: `${ov.inbox} proposals waiting` },
    { ok: inReview === 0, label: "Every item baselined", detail: `${inReview} items still Draft or In Review appear as open` },
  ];
  const stamp = new Date().toISOString().slice(0, 10).replace(/-/g, "");

  return (
    <>
      <PageHeader title="Export" subtitle="The supplier handoff is generated from the register at download time." />
      <div className="export-grid">
        <div className="card export-card">
          <FileText size={22} className="export-icon" />
          <h3>System requirements specification</h3>
          <p className="muted">Word · document control, scope and companion principles, requirements by group, cognitive coverage, verification matrix, open points, change record.</p>
          <code className="export-file">SEW1-IVA-specification-{stamp}.docx</code>
          <a className="btn btn-primary btn-md" href="/api/export/word"><Download size={14} /><span>Download Word</span></a>
        </div>
        <div className="card export-card">
          <FileSpreadsheet size={22} className="export-icon" />
          <h3>Requirements workbook</h3>
          <p className="muted">Excel · Requirements, Traceability, Cognitive coverage, Open items, Run log.</p>
          <code className="export-file">SEW1-IVA-requirements-{stamp}.xlsx</code>
          <a className="btn btn-primary btn-md" href="/api/export/excel"><Download size={14} /><span>Download Excel</span></a>
        </div>
        <div className="card readiness">
          <h3>Supplier issue readiness</h3>
          <p className="muted">Export is always available. These checks say whether it is ready to issue.</p>
          <ul>
            {checks.map((c) => (
              <li key={c.label} className={c.ok ? "ok" : "todo"}>
                {c.ok ? <CheckCircle2 size={15} /> : <CircleAlert size={15} />}
                <div><div>{c.label}</div><div className="muted">{c.detail}</div></div>
              </li>
            ))}
          </ul>
          <div className="readiness-foot">{ov.requirements} requirements included</div>
        </div>
      </div>
    </>
  );
}
