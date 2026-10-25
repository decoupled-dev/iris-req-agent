import { useEffect, useMemo, useState } from "react";
import { Check, CheckCheck, Inbox, Pencil, Search, X } from "lucide-react";
import { api, InboxItem } from "../api";
import { usePoll } from "../hooks";
import { Button, CategoryTag, Chip, Empty, Field, Kbd, PageHeader, Segmented } from "../components/ui";
import Scenario from "../components/Scenario";

const AGENT_LABEL: Record<string, string> = {
  requirements_synthesis: "Synthesis",
  gdpr_privacy: "Privacy",
  driver_distraction: "Distraction",
  safety_cybersecurity: "Safety & security",
};

export default function Review({ initial = null }: { initial?: number | null }) {
  const inbox = usePoll(api.inbox, 4000);
  const findings = usePoll(api.findings, 0);
  const [agent, setAgent] = useState("all");
  const [q, setQ] = useState("");
  const [selected, setSelected] = useState<number | null>(initial);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState("");
  const [error, setError] = useState<string | null>(null);

  const items = inbox.data ?? [];
  const visible = useMemo(
    () => items.filter((i) => (agent === "all" || i.agent_id === agent)
      && `${i.proposal.title} ${i.proposal.statement} ${i.proposal.category}`.toLowerCase().includes(q.toLowerCase())),
    [items, agent, q],
  );
  const current = visible.find((i) => i.pk === selected) ?? visible[0];

  useEffect(() => {
    setEditing(false);
    setDraft(current?.proposal.statement ?? "");
  }, [current?.pk]);

  const advance = () => {
    const idx = visible.findIndex((i) => i.pk === current?.pk);
    const next = visible[idx + 1] ?? visible[idx - 1];
    setSelected(next?.pk ?? null);
  };

  const decide = (fn: () => Promise<unknown>) =>
    fn().then(() => {
      setError(null);
      advance();
      inbox.refresh();
    }).catch((e: Error) => setError(e.message));

  const accept = (state: string) => current && decide(() =>
    api.accept(current.pk, state, editing && draft !== current.proposal.statement ? { statement: draft } : undefined));
  const reject = () => current && decide(() => api.reject(current.pk));

  useEffect(() => {
    const on = (e: KeyboardEvent) => {
      if ((e.target as HTMLElement).closest("input, textarea")) return;
      const idx = visible.findIndex((i) => i.pk === current?.pk);
      if (e.key === "j") setSelected(visible[Math.min(idx + 1, visible.length - 1)]?.pk ?? null);
      else if (e.key === "k") setSelected(visible[Math.max(idx - 1, 0)]?.pk ?? null);
      else if (e.key === "a") accept("Draft");
      else if (e.key === "i") accept("In Review");
      else if (e.key === "r") reject();
      else if (e.key === "e") setEditing(true);
      else return;
      e.preventDefault();
    };
    window.addEventListener("keydown", on);
    return () => window.removeEventListener("keydown", on);
  });

  const counts = items.reduce<Record<string, number>>((m, i) => ({ ...m, [i.agent_id]: (m[i.agent_id] ?? 0) + 1 }), {});
  const acceptAll = () => {
    if (!visible.length || !confirm(`Accept ${visible.length} proposals as Draft?`)) return;
    api.bulk(visible.map((i) => i.pk), "accept").then(() => inbox.refresh()).catch((e: Error) => setError(e.message));
  };

  return (
    <>
      <PageHeader
        title="Review"
        subtitle={<>Accept or reject agent proposals. Nothing enters the register without a reviewer. <span className="kbd-hint"><Kbd>J</Kbd><Kbd>K</Kbd> move · <Kbd>A</Kbd> draft · <Kbd>I</Kbd> in review · <Kbd>R</Kbd> reject · <Kbd>E</Kbd> edit</span></>}
        actions={<Button icon={<CheckCheck size={14} />} disabled={!visible.length} onClick={acceptAll}>Accept all shown</Button>}
      />
      {error && <div className="alert alert-danger">{error}</div>}
      {!items.length ? (
        <div className="card"><Empty icon={<Inbox size={22} />} title="Inbox is clear">Run the pipeline to generate proposals.</Empty></div>
      ) : (
        <div className="review">
          <div className="review-list card">
            <div className="review-filters">
              <div className="search"><Search size={14} /><input placeholder="Filter proposals" value={q} onChange={(e) => setQ(e.target.value)} /></div>
              <Segmented value={agent} onChange={setAgent} options={[
                { value: "all", label: "All", count: items.length },
                ...Object.keys(AGENT_LABEL).filter((a) => counts[a]).map((a) => ({ value: a, label: AGENT_LABEL[a], count: counts[a] })),
              ]} />
            </div>
            <ul>
              {visible.map((i) => (
                <li key={i.pk} className={i.pk === current?.pk ? "active" : ""} onClick={() => setSelected(i.pk)}>
                  <div className="rl-top">
                    <CategoryTag category={i.proposal.category} />
                    {i.proposal.id && <span className="rl-update">Update {i.proposal.id}</span>}
                    {i.proposal.scenario && <span className="gwt-badge" title="Has a GIVEN/WHEN/THEN scenario">GWT</span>}
                    <span className="rl-agent">{AGENT_LABEL[i.agent_id]}</span>
                  </div>
                  <div className="rl-title">{i.proposal.title}</div>
                </li>
              ))}
            </ul>
          </div>
          {current ? <Detail item={current} findings={findings.data ?? {}} editing={editing} draft={draft}
            setDraft={setDraft} setEditing={setEditing} accept={accept} reject={reject} /> : <div className="card"><Empty title="No match" /></div>}
        </div>
      )}
    </>
  );
}

function Detail({ item, findings, editing, draft, setDraft, setEditing, accept, reject }: {
  item: InboxItem;
  findings: Record<string, { title: string; statement: string; agent_id: string; source: string }>;
  editing: boolean; draft: string; setDraft: (s: string) => void; setEditing: (b: boolean) => void;
  accept: (s: string) => void; reject: () => void;
}) {
  const p = item.proposal;
  const sources = p.source.split(",").map((s) => s.trim()).filter(Boolean);
  return (
    <div className="review-detail card">
      <div className="rd-head">
        <div className="rd-tags">
          <CategoryTag category={p.category} />
          <Chip>{p.priority}</Chip>
          {p.preliminary_asil && <Chip tone="warning">ASIL {p.preliminary_asil} · preliminary</Chip>}
          {p.id && <Chip tone="info">New version of {p.id}</Chip>}
        </div>
        <h2>{p.title}</h2>
        <div className="rd-from">Proposed by {AGENT_LABEL[item.agent_id]} · run <code>{item.run_id}</code></div>
      </div>

      <div className="rd-statement">
        {editing ? (
          <textarea value={draft} onChange={(e) => setDraft(e.target.value)} rows={4} autoFocus />
        ) : (
          <p>{draft}</p>
        )}
        {!editing && <button className="link-btn" onClick={() => setEditing(true)}><Pencil size={12} /> Edit before accepting</button>}
      </div>

      {p.scenario && (
        <div className="rd-gwt">
          <div className="field-label">Behaviour specification</div>
          <Scenario scenario={p.scenario} />
        </div>
      )}

      <div className="rd-grid">
        <Field label="Rationale">{p.rationale}</Field>
        <Field label="Acceptance criteria">{p.acceptance_criteria || <span className="muted">Missing</span>}</Field>
        <Field label="Verification">{p.verification_method}</Field>
        <Field label="Cognitive capability">
          {p.cognitive_capability.length ? p.cognitive_capability.map((c) => <Chip key={c} tone="accent">{c}</Chip>) : <span className="muted">—</span>}
        </Field>
        <Field label="Standards">
          {p.standard_references.length ? p.standard_references.map((s) => <Chip key={s}>{s}</Chip>) : <span className="muted">—</span>}
        </Field>
        {p.asil_note && <Field label="ASIL note">{p.asil_note}</Field>}
      </div>

      <div className="rd-sources">
        <div className="field-label">Traced findings</div>
        {sources.map((s) => {
          const f = findings[s];
          return (
            <div key={s} className="source">
              <code>{s}</code>
              {f ? <><b>{f.title}</b><span>{f.statement}</span></> : <span className="muted">Finding not in the latest runs</span>}
            </div>
          );
        })}
      </div>

      <div className="rd-actions">
        <Button variant="primary" icon={<Check size={14} />} onClick={() => accept("Draft")}>Accept as Draft</Button>
        <Button onClick={() => accept("In Review")}>Accept as In Review</Button>
        <span className="spacer" />
        <Button variant="danger" icon={<X size={14} />} onClick={reject}>Reject</Button>
      </div>
    </div>
  );
}
