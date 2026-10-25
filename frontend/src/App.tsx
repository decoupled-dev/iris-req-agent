import { Boxes, Brain, Download, FileText, History, Inbox, Workflow } from "lucide-react";
import { api } from "./api";
import { useHashRoute, usePoll } from "./hooks";
import Pipeline from "./pages/Pipeline";
import Review from "./pages/Review";
import Requirements from "./pages/Requirements";
import Cognition from "./pages/Cognition";
import Runs from "./pages/Runs";
import Export from "./pages/Export";

const NAV = [
  { id: "pipeline", label: "Pipeline", icon: Workflow },
  { id: "review", label: "Review", icon: Inbox },
  { id: "requirements", label: "Requirements", icon: FileText },
  { id: "cognition", label: "Cognitive coverage", icon: Brain },
  { id: "runs", label: "Run log", icon: History },
  { id: "export", label: "Export", icon: Download },
];

export default function App() {
  const [route, go] = useHashRoute();
  const { data: ov } = usePoll(api.overview, 3000);
  const { data: rt } = usePoll(api.runtime, 0);

  const page = (() => {
    switch (route) {
      case "review": return <Review />;
      case "requirements": return <Requirements />;
      case "cognition": return <Cognition />;
      case "runs": return <Runs />;
      case "export": return <Export />;
      default: return <Pipeline go={go} />;
    }
  })();

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><Boxes size={16} /></div>
          <div>
            <div className="brand-name">SEW1 Workbench</div>
            <div className="brand-sub">In-car AI companion</div>
          </div>
        </div>
        <nav>
          {NAV.map(({ id, label, icon: Icon }) => (
            <a key={id} href={`#/${id}`} className={route === id || (route === "" && id === "pipeline") ? "active" : ""}>
              <Icon size={16} />
              <span>{label}</span>
              {id === "review" && !!ov?.inbox && <span className="nav-badge">{ov.inbox}</span>}
              {id === "cognition" && ov && <span className="nav-level">{ov.specified_cognitive_level}</span>}
            </a>
          ))}
        </nav>
        <div className="sidebar-foot">
          <div className="runtime">
            <span className={`runtime-dot ${rt?.provider === "simulated" ? "sim" : "live"}`} />
            <div>
              <div className="runtime-label">{rt?.provider === "simulated" ? "Simulated runtime" : rt?.provider ?? "…"}</div>
              <div className="runtime-model">{rt?.model}</div>
            </div>
          </div>
          <div className="project">In-car voice assistant · AAOS or QNX</div>
        </div>
      </aside>
      <main className="content">{page}</main>
    </div>
  );
}
