export function duration(start?: string | null, end?: string | null): string {
  if (!start) return "—";
  const ms = (end ? Date.parse(end) : Date.now()) - Date.parse(start);
  if (ms < 1000) return `${Math.max(ms, 0)} ms`;
  const s = ms / 1000;
  return s < 60 ? `${s.toFixed(1)} s` : `${Math.floor(s / 60)}m ${Math.round(s % 60)}s`;
}

export function tokens(n?: number): string {
  if (!n) return "0";
  return n >= 1000 ? `${(n / 1000).toFixed(n >= 10000 ? 0 : 1)}k` : String(n);
}

export function time(ts?: string | null): string {
  if (!ts) return "—";
  return new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

export function relative(ts?: string | null): string {
  if (!ts) return "never";
  const s = (Date.now() - Date.parse(ts)) / 1000;
  if (s < 60) return "just now";
  if (s < 3600) return `${Math.floor(s / 60)} min ago`;
  if (s < 86400) return `${Math.floor(s / 3600)} h ago`;
  return new Date(ts).toLocaleDateString();
}

export const LEVELS = ["CL1", "CL2", "CL3", "CL4", "CL5"];
export const LEVEL_NAMES: Record<string, string> = {
  CL0: "Command",
  CL1: "Conversational",
  CL2: "Situated",
  CL3: "Personal",
  CL4: "Proactive partner",
  CL5: "Companion",
};
export const levelIndex = (l?: string) => (l ? Number(l.replace("CL", "")) : 0);
