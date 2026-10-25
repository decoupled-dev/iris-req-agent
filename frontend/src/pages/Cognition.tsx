import { Check, Circle } from "lucide-react";
import { api } from "../api";
import { usePoll } from "../hooks";
import { LEVELS, LEVEL_NAMES, levelIndex } from "../format";
import { LevelMeter, PageHeader } from "../components/ui";

const LEVEL_DESC: Record<string, string> = {
  CL1: "Natural phrasing, follow-ups, repair questions",
  CL2: "Seat attribution, vehicle grounding, trip memory, action tiers",
  CL3: "Inspectable long-term memory, reversible learning",
  CL4: "Workload awareness, proactive suggestions, planning, explanations",
  CL5: "Episodic recall, persona, opt-in affect, open conversation",
};

export default function Cognition() {
  const { data } = usePoll(api.cognition, 5000);
  if (!data) return null;
  const spec = levelIndex(data.specified);
  const caps = data.capabilities;
  const covered = caps.filter((c) => c.covered).length;

  return (
    <>
      <PageHeader title="Cognitive coverage"
        subtitle="A level is specified when every capability at and below it has an included, verifiable requirement." />
      <div className="card cog-summary">
        <div>
          <div className="stat-label">Specified level</div>
          <div className="cog-level">{data.specified} <span>{LEVEL_NAMES[data.specified]}</span></div>
          <LevelMeter specified={data.specified} target={data.target} />
        </div>
        <div className="cog-summary-side">
          <div><span className="stat-label">Target</span><b>{data.target} {LEVEL_NAMES[data.target]}</b></div>
          <div><span className="stat-label">Capabilities covered</span><b>{covered} / {caps.length}</b></div>
        </div>
      </div>

      <div className="ladder">
        {LEVELS.map((l, i) => {
          const at = caps.filter((c) => c.level === l);
          const done = at.filter((c) => c.covered).length;
          const state = i < spec ? "done" : done > 0 ? "partial" : "todo";
          return (
            <div key={l} className={`rung rung-${state}`}>
              <div className="rung-head">
                <span className="rung-id">{l}</span>
                <span className="rung-name">{LEVEL_NAMES[l]}</span>
                <span className="rung-count">{done}/{at.length}</span>
              </div>
              <div className="rung-desc">{LEVEL_DESC[l]}</div>
              <ul className="caps">
                {at.map((c) => (
                  <li key={c.id} className={c.covered ? "covered" : ""}>
                    {c.covered ? <Check size={13} /> : <Circle size={13} />}
                    <div>
                      <div className="cap-title"><code>{c.id}</code> {c.title}</div>
                      <div className="cap-meta">{c.faculty}{c.covered && <> · {c.requirement_ids.join(", ")}</>}</div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          );
        })}
      </div>
    </>
  );
}
