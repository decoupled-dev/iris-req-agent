import { useEffect, useState } from "react";
import { ArrowRight, Ban, FileCode2, ListTree, Play, RotateCw, Sparkles } from "lucide-react";
import { Agent, api, Overview, Prompt, Run } from "../api";
import { usePoll } from "../hooks";
import { duration, LEVEL_NAMES, tokens } from "../format";
import { Button, Chip, LevelMeter, PageHeader, Segmented, Stat, StatusPill } from "../components/ui";
import Trace from "../components/Trace";

const STAGES = [
  { id: "research", label: "Research", hint: "Parallel" },
  { id: "synthesis", label: "Synthesis", hint: "Merge" },
  { id: "assurance", label: "Assurance", hint: "Parallel" },
  { id: "gate", label: "Gate", hint: "Check" },
];

export default function Pipeline({ go }: { go: (r: string) => void }) {
  const agents = usePoll(api.agents, 1000);
  const overview = usePoll(api.overview, 1500);
  const [selected, setSelected] = useState<string>("companion_cognition");
  const [error, setError] = useState<string | null>(null);

  const ov = overview.data;
  const list = agents.data ?? [];
  const busy = ov?.cycle_running || list.some((a) => a.latest_run && ["queued", "running"].includes(a.latest_run.status));
  const agent = list.find((a) => a.id === selected);

  const act = (fn: () => Promise<unknown>) =>
    fn()
      .then(() => {
        setError(null);
        agents.refresh();
        overview.refresh();
      })
      .catch((e: Error) => setError(e.message));

  return (
    <>
      <PageHeader
        title="Pipeline"
        subtitle="Research, synthesise, assure and gate the SEW1 requirement baseline."
        actions={
          <Button variant="primary" icon={<Play size={14} />} disabled={busy} onClick={() => act(api.startPipeline)}>
            {busy ? "Cycle running…" : "Run full cycle"}
          </Button>
        }
      />
      {error && <div className="alert alert-danger">{error}</div>}
      <KpiRow ov={ov} go={go} />

      <div className="pipeline-layout">
        <div className="board">
          {STAGES.map((stage, i) => (
            <div key={stage.id} className="stage">
              <div className="stage-head">
                <span className="stage-index">{i + 1}</span>
                <span className="stage-label">{stage.label}</span>
                <span className="stage-hint">{stage.hint}</span>
                {i < STAGES.length - 1 && <ArrowRight size={14} className="stage-arrow" />}
              </div>
              <div className="stage-body">
                {list.filter((a) => a.stage === stage.id).map((a) => (
                  <AgentNode key={a.id} agent={a} selected={a.id === selected} onSelect={() => setSelected(a.id)}
                    onRun={() => act(() => api.startAgent(a.id))}
                    onCancel={() => a.latest_run && act(() => api.cancel(a.latest_run!.run_id))} />
                ))}
              </div>
            </div>
          ))}
        </div>
        {agent && <AgentPanel agent={agent} onRun={() => act(() => api.startAgent(agent.id))} />}
      </div>
    </>
  );
}

function KpiRow({ ov, go }: { ov: Overview | null; go: (r: string) => void }) {
  if (!ov) return <div className="kpis skeleton" />;
  const sev = ov.gate?.by_severity ?? {};
  return (
    <div className="kpis">
      <Stat label="Cognitive level" onClick={() => go("cognition")}
        value={<>{ov.specified_cognitive_level}<span className="stat-of"> / {ov.target_cognitive_level}</span></>}
        sub={`${LEVEL_NAMES[ov.specified_cognitive_level]} · target ${LEVEL_NAMES[ov.target_cognitive_level]}`}>
        <LevelMeter specified={ov.specified_cognitive_level} target={ov.target_cognitive_level} />
      </Stat>
      <Stat label="Requirements" value={ov.requirements} onClick={() => go("requirements")}
        sub={["Draft", "In Review", "Baselined"].map((s) => `${ov.by_state[s] ?? 0} ${s.toLowerCase()}`).join(" · ")} />
      <Stat label="Awaiting review" value={ov.inbox} onClick={() => go("review")}
        sub={ov.inbox ? "Proposals in the inbox" : "Inbox clear"} />
      <Stat label="Gate findings" value={ov.gate ? ov.gate.findings : "—"}
        sub={ov.gate ? `${sev.critical ?? 0} critical · ${(ov.gate.uncovered ?? []).length} uncovered capabilities` : "Gate has not run"} />
      <Stat label="Model usage" value={tokens(ov.tokens)} onClick={() => go("runs")} sub={`${ov.runs} agent runs`} />
    </div>
  );
}

function AgentNode({ agent, selected, onSelect, onRun, onCancel }: {
  agent: Agent; selected: boolean; onSelect: () => void; onRun: () => void; onCancel: () => void;
}) {
  const run = agent.latest_run;
  const status = run?.status ?? "idle";
  const active = status === "queued" || status === "running";
  const m = run?.result?.metrics;
  return (
    <div className={`node node-${status} ${selected ? "selected" : ""}`} onClick={onSelect}>
      <div className="node-top">
        <span className="node-name">{agent.name}</span>
        <StatusPill status={status} />
      </div>
      <div className="node-desc">{agent.description}</div>
      <div className="node-foot">
        <span className="node-meta">
          {run ? (
            <>
              {duration(run.started, run.finished)}
              {m?.turns ? <> · {m.turns} turns</> : null}
              {m?.input_tokens ? <> · {tokens((m.input_tokens ?? 0) + (m.output_tokens ?? 0))} tok</> : null}
            </>
          ) : "Not run"}
        </span>
        <span onClick={(e) => e.stopPropagation()}>
          {active ? (
            <button className="icon-btn" title="Cancel" onClick={onCancel}><Ban size={14} /></button>
          ) : (
            <button className="icon-btn" title={run ? "Rerun" : "Run"} onClick={onRun}>
              {run ? <RotateCw size={14} /> : <Play size={14} />}
            </button>
          )}
        </span>
      </div>
    </div>
  );
}

type PanelTab = "trace" | "output" | "prompt";

function AgentPanel({ agent, onRun }: { agent: Agent; onRun: () => void }) {
  const [tab, setTab] = useState<PanelTab>("trace");
  const run = agent.latest_run;
  const [fresh, setFresh] = useState<Run | null>(null);
  useEffect(() => {
    if (run) api.run(run.run_id).then(setFresh);
    else setFresh(null);
  }, [run?.run_id, run?.status]);
  const m = run?.result?.metrics;

  return (
    <aside className="panel">
      <header className="panel-head">
        <div>
          <div className="panel-title">{agent.name}</div>
          <div className="panel-sub">
            {run ? <><code>{run.run_id}</code> · {agent.mode}</> : `${agent.stage} stage · ${agent.mode}`}
          </div>
        </div>
        {run && <StatusPill status={run.status} />}
      </header>
      {run && (
        <div className="panel-metrics">
          <div><span>Model</span><b>{m?.model ?? "—"}</b></div>
          <div><span>Duration</span><b>{duration(run.started, run.finished)}</b></div>
          <div><span>Turns</span><b>{m?.turns ?? "—"}</b></div>
          <div><span>Tokens</span><b>{m?.input_tokens ? `${tokens(m.input_tokens)} / ${tokens(m.output_tokens)}` : "—"}</b></div>
        </div>
      )}
      <div className="panel-tabs">
        <Segmented<PanelTab> value={tab} onChange={setTab} options={[
          { value: "trace", label: "Trace" },
          { value: "output", label: "Output", count: run?.result ? run.result.findings.length + run.result.proposals.length : undefined },
          { value: "prompt", label: "Prompt & tools" },
        ]} />
      </div>
      <div className="panel-body">
        {!run && tab !== "prompt" ? (
          <div className="panel-empty">
            <Sparkles size={20} />
            <p>This agent has not run yet.</p>
            <Button variant="primary" size="sm" icon={<Play size={13} />} onClick={onRun}>Run agent</Button>
          </div>
        ) : tab === "trace" && run ? (
          <Trace run={run} />
        ) : tab === "output" ? (
          <Output run={fresh ?? run} publishes={agent.publishes} />
        ) : (
          <PromptView agentId={agent.id} />
        )}
      </div>
    </aside>
  );
}

function Output({ run, publishes }: { run: Run | null; publishes: boolean }) {
  if (!run?.result) return <div className="trace-empty">No output yet.</div>;
  const { findings, proposals, metrics } = run.result;
  return (
    <div className="output">
      <p className="output-summary">{run.summary}</p>
      {metrics.specified_cognitive_level && (
        <Chip tone="accent">Specified level {String(metrics.specified_cognitive_level)}</Chip>
      )}
      {proposals.length > 0 && (
        <section>
          <h4>
            <FileCode2 size={13} /> Proposals <span className="muted">{proposals.length}</span>
            <span className="output-note">{publishes ? "Published to review inbox" : "Candidates for synthesis"}</span>
          </h4>
          <ul className="output-list">
            {proposals.map((p, i) => (
              <li key={i}>
                <div className="ol-head"><span className="ol-cat">{p.id || p.category}</span>{p.title}</div>
                <div className="ol-body">{p.statement}</div>
              </li>
            ))}
          </ul>
        </section>
      )}
      {findings.length > 0 && (
        <section>
          <h4><ListTree size={13} /> Findings <span className="muted">{findings.length}</span></h4>
          <ul className="output-list">
            {findings.map((f) => (
              <li key={f.id}>
                <div className="ol-head"><code>{f.id}</code>{f.title}</div>
                <div className="ol-body">{f.statement}</div>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}

function PromptView({ agentId }: { agentId: string }) {
  const [p, setP] = useState<Prompt | null>(null);
  useEffect(() => void api.prompt(agentId).then(setP), [agentId]);
  if (!p) return null;
  return (
    <div className="output">
      <section>
        <h4>Tools <span className="muted">{p.tools.length}</span></h4>
        <ul className="output-list">
          {p.tools.map((t) => (
            <li key={t.name}>
              <div className="ol-head"><code>{t.name}</code></div>
              <div className="ol-body">{t.description}</div>
            </li>
          ))}
        </ul>
      </section>
      <section>
        <h4>System prompt</h4>
        <pre className="prompt">{p.system}</pre>
      </section>
    </div>
  );
}
