import { useState } from "react";
import { History } from "lucide-react";
import { api, Run } from "../api";
import { usePoll } from "../hooks";
import { duration, time, tokens } from "../format";
import { Drawer, Empty, PageHeader, StatusPill } from "../components/ui";
import Trace from "../components/Trace";

export default function Runs() {
  const runs = usePoll(api.runs, 2000);
  const [open, setOpen] = useState<Run | null>(null);
  const rows = [...(runs.data ?? [])].reverse();
  const live = open ? rows.find((r) => r.run_id === open.run_id) ?? open : null;

  return (
    <>
      <PageHeader title="Run log" subtitle="Every agent run is kept, including failed and cancelled ones." />
      <div className="card">
        {!rows.length ? <Empty icon={<History size={22} />} title="No runs yet" /> : (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr><th>Run</th><th>Agent</th><th>Status</th><th>Model</th><th className="num">Turns</th><th className="num">Tokens</th><th className="num">Duration</th><th>Started</th><th>Summary</th></tr>
              </thead>
              <tbody>
                {rows.map((r) => {
                  const m = r.result?.metrics;
                  return (
                    <tr key={r.run_id} onClick={() => setOpen(r)}>
                      <td className="mono">{r.run_id}</td>
                      <td className="nowrap">{r.agent_id.replace(/_/g, " ")}</td>
                      <td><StatusPill status={r.status} /></td>
                      <td className="mono muted">{m?.model ?? r.mode}</td>
                      <td className="num">{m?.turns ?? "—"}</td>
                      <td className="num">{m?.input_tokens ? tokens(m.input_tokens + (m.output_tokens ?? 0)) : "—"}</td>
                      <td className="num">{duration(r.started, r.finished)}</td>
                      <td className="muted nowrap">{time(r.started)}</td>
                      <td className="summary-cell">{r.summary}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
      <Drawer open={!!live} onClose={() => setOpen(null)} width={620}
        title={live && <><span className="mono">{live.run_id}</span> {live.agent_id.replace(/_/g, " ")}</>}>
        {live && <Trace run={live} />}
      </Drawer>
    </>
  );
}
