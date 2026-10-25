import { useEffect, useMemo, useRef, useState } from "react";
import { AlertTriangle, Ban, Brain, CheckCircle2, ChevronRight, MessageSquare, Play, Wrench } from "lucide-react";
import { api, Run, RunEvent } from "../api";
import { tokens, time } from "../format";

/** Live trace of one agent run: model turns, reasoning, tool calls and results. */
export default function Trace({ run }: { run: Run }) {
  const [events, setEvents] = useState<RunEvent[]>([]);
  const last = useRef(0);
  const bottom = useRef<HTMLDivElement>(null);
  const live = run.status === "running" || run.status === "queued";

  useEffect(() => {
    setEvents([]);
    last.current = 0;
  }, [run.run_id]);

  useEffect(() => {
    let stop = false;
    const tick = () =>
      api.events(run.run_id, last.current).then((evs) => {
        if (stop || !evs.length) return;
        last.current = evs[evs.length - 1].seq;
        setEvents((prev) => [...prev, ...evs]);
      });
    tick();
    if (!live) return () => void (stop = true);
    const t = setInterval(tick, 500);
    return () => {
      stop = true;
      clearInterval(t);
    };
  }, [run.run_id, live]);

  useEffect(() => {
    if (live) bottom.current?.scrollIntoView({ block: "end", behavior: "smooth" });
  }, [events.length, live]);

  // Pair each tool_call with its tool_result so they render as one step.
  const results = useMemo(() => {
    const m = new Map<string, RunEvent>();
    events.forEach((e) => e.type === "tool_result" && m.set(e.data.id, e));
    return m;
  }, [events]);

  if (!events.length) {
    return <div className="trace-empty">{live ? "Waiting for the first model turn…" : "No trace recorded for this run."}</div>;
  }

  return (
    <ol className="trace">
      {events.map((e) => {
        switch (e.type) {
          case "start":
            return (
              <li key={e.seq} className="t-row t-start">
                <Play size={13} />
                <span>
                  Session started on <b>{e.data.provider}</b>
                  {e.data.model && <> · <code>{e.data.model}</code></>}
                  {e.data.tools && <> · {e.data.tools.length} tools</>}
                </span>
                <time>{time(e.ts)}</time>
              </li>
            );
          case "turn":
            return (
              <li key={e.seq} className="t-turn">
                <span>Turn {e.data.n}</span>
                <span className="t-turn-meta">
                  {e.data.latency_ms} ms · {tokens(e.data.input_tokens)} in · {tokens(e.data.output_tokens)} out
                </span>
              </li>
            );
          case "thinking":
            return (
              <li key={e.seq} className="t-row t-thinking">
                <Brain size={13} />
                <p>{e.data.text}</p>
              </li>
            );
          case "message":
            return (
              <li key={e.seq} className="t-row t-message">
                <MessageSquare size={13} />
                <p>{e.data.text}</p>
              </li>
            );
          case "tool_call":
            return <ToolStep key={e.seq} call={e} result={results.get(e.data.id)} />;
          case "result":
            return (
              <li key={e.seq} className="t-row t-result">
                <CheckCircle2 size={14} />
                <div>
                  <p>{e.data.summary}</p>
                  <div className="t-result-meta">
                    {e.data.findings} findings · {e.data.proposals} proposals ·{" "}
                    {tokens(e.data.input_tokens + e.data.output_tokens)} tokens
                  </div>
                </div>
              </li>
            );
          case "error":
            return (
              <li key={e.seq} className="t-row t-error">
                <AlertTriangle size={14} />
                <p>{e.data.message}</p>
              </li>
            );
          case "cancelled":
            return (
              <li key={e.seq} className="t-row t-error">
                <Ban size={14} />
                <p>Cancelled by engineer.</p>
              </li>
            );
          default:
            return null;
        }
      })}
      {live && <li className="t-live"><span className="pulse" /> Agent working</li>}
      <div ref={bottom} />
    </ol>
  );
}

function ToolStep({ call, result }: { call: RunEvent; result?: RunEvent }) {
  const [open, setOpen] = useState(false);
  const isSubmit = call.data.name === "submit_result";
  const args = isSubmit
    ? `${call.data.input.findings?.length ?? 0} findings, ${call.data.input.proposals?.length ?? 0} proposals`
    : Object.entries(call.data.input as Record<string, unknown>).map(([k, v]) => `${k}=${JSON.stringify(v)}`).join(", ");
  const error = result?.data.is_error;
  return (
    <li className={`t-row t-tool ${error ? "is-error" : ""}`}>
      <Wrench size={13} />
      <div className="t-tool-body">
        <button className="t-tool-head" onClick={() => setOpen(!open)} disabled={!result && !isSubmit}>
          <ChevronRight size={12} className={open ? "rot" : ""} />
          <code className="t-tool-name">{call.data.name}</code>
          <span className="t-tool-args">({args})</span>
          {!result && !isSubmit && <span className="t-tool-pending">running</span>}
        </button>
        {open && (
          <pre className="t-tool-out">
            {isSubmit ? JSON.stringify(call.data.input, null, 2) : result?.data.preview}
          </pre>
        )}
      </div>
    </li>
  );
}
