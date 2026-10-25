import { ReactNode } from "react";
import { Loader2, X } from "lucide-react";
import type { RunStatus } from "../api";
import { LEVELS, LEVEL_NAMES, levelIndex } from "../format";

export function Button({
  children, onClick, variant = "secondary", size = "md", disabled, icon, title, type = "button",
}: {
  children?: ReactNode;
  onClick?: () => void;
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md";
  disabled?: boolean;
  icon?: ReactNode;
  title?: string;
  type?: "button" | "submit";
}) {
  return (
    <button type={type} className={`btn btn-${variant} btn-${size}`} onClick={onClick} disabled={disabled} title={title}>
      {icon}
      {children && <span>{children}</span>}
    </button>
  );
}

const STATUS_LABEL: Record<RunStatus, string> = {
  idle: "Idle", queued: "Queued", running: "Running", succeeded: "Succeeded", failed: "Failed", cancelled: "Cancelled",
};

export function StatusPill({ status }: { status: RunStatus }) {
  return (
    <span className={`pill pill-${status}`}>
      {status === "running" ? <Loader2 size={11} className="spin" /> : <span className="dot" />}
      {STATUS_LABEL[status]}
    </span>
  );
}

const STATE_TONE: Record<string, string> = {
  Draft: "neutral", "In Review": "warning", Baselined: "success", Superseded: "muted", Rejected: "danger", Proposed: "info",
};

export function StateBadge({ state }: { state: string }) {
  return <span className={`badge badge-${STATE_TONE[state] ?? "neutral"}`}>{state}</span>;
}

export function CategoryTag({ category }: { category: string }) {
  return <span className={`tag tag-${category.replace("SYS-", "").toLowerCase()}`}>{category}</span>;
}

export function Chip({ children, tone = "neutral" }: { children: ReactNode; tone?: string }) {
  return <span className={`chip chip-${tone}`}>{children}</span>;
}

export function Kbd({ children }: { children: ReactNode }) {
  return <kbd className="kbd">{children}</kbd>;
}

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: ReactNode; actions?: ReactNode }) {
  return (
    <div className="page-header">
      <div>
        <h1>{title}</h1>
        {subtitle && <p className="page-subtitle">{subtitle}</p>}
      </div>
      {actions && <div className="page-actions">{actions}</div>}
    </div>
  );
}

export function Stat({ label, value, sub, onClick, children }: {
  label: string; value: ReactNode; sub?: ReactNode; onClick?: () => void; children?: ReactNode;
}) {
  return (
    <div className={`stat ${onClick ? "stat-link" : ""}`} onClick={onClick}>
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      {children}
      {sub && <div className="stat-sub">{sub}</div>}
    </div>
  );
}

export function LevelMeter({ specified, target }: { specified: string; target: string }) {
  const s = levelIndex(specified), t = levelIndex(target);
  return (
    <div className="level-meter" title={`${specified} ${LEVEL_NAMES[specified]} of target ${target}`}>
      {LEVELS.map((l, i) => (
        <span key={l} className={`seg ${i < s ? "on" : ""} ${i + 1 > t ? "beyond" : ""}`} />
      ))}
    </div>
  );
}

export function Empty({ icon, title, children }: { icon?: ReactNode; title: string; children?: ReactNode }) {
  return (
    <div className="empty">
      {icon && <div className="empty-icon">{icon}</div>}
      <div className="empty-title">{title}</div>
      {children && <div className="empty-body">{children}</div>}
    </div>
  );
}

export function Drawer({ open, onClose, title, children, width = 560 }: {
  open: boolean; onClose: () => void; title: ReactNode; children: ReactNode; width?: number;
}) {
  if (!open) return null;
  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <aside className="drawer" style={{ width }} onClick={(e) => e.stopPropagation()}>
        <header className="drawer-header">
          <div className="drawer-title">{title}</div>
          <button className="icon-btn" onClick={onClose} aria-label="Close"><X size={16} /></button>
        </header>
        <div className="drawer-body">{children}</div>
      </aside>
    </div>
  );
}

export function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="field">
      <div className="field-label">{label}</div>
      <div className="field-value">{children}</div>
    </div>
  );
}

export function Segmented<T extends string>({ value, options, onChange }: {
  value: T; options: { value: T; label: string; count?: number }[]; onChange: (v: T) => void;
}) {
  return (
    <div className="segmented">
      {options.map((o) => (
        <button key={o.value} className={o.value === value ? "active" : ""} onClick={() => onChange(o.value)}>
          {o.label}
          {o.count !== undefined && <span className="count">{o.count}</span>}
        </button>
      ))}
    </div>
  );
}
