// Typed client for backend/app/main.py.

export type RunStatus = "idle" | "queued" | "running" | "succeeded" | "failed" | "cancelled";
export type ReqState = "Draft" | "In Review" | "Baselined" | "Superseded" | "Rejected" | "Proposed";

export interface Finding {
  id: string;
  title: string;
  statement: string;
  source: string;
  confidence: string;
}

export interface Condition {
  signal: string;
  op: string;
  value?: unknown;
  note?: string;
}

export interface ScenarioResponse {
  type: "ACT" | "CONFIRM_THEN_ACT" | "ASK" | "SUGGEST" | "INFORM" | "DEFER" | "REFUSE";
  target?: string;
  zone?: string;
  value?: unknown;
  say?: string;
  note?: string;
}

export interface Scenario {
  given: Condition[];
  when: { trigger: string; intent?: string; example?: string };
  then: ScenarioResponse[];
}

export interface Signal {
  alias: string;
  label: string;
  domain: string;
  vss: string;
  vhal: string;
  type: string;
  unit?: string;
  range?: number[];
  enum?: string[];
  access: "read" | "actuator";
  tier?: "comfort" | "high-impact" | "prohibited";
  availability?: "optional";
  privacy?: "personal" | "biometric";
  family?: string;
  zone?: string;
  note?: string;
  used_by: string[];
}

export interface Trigger {
  id: string;
  kind: "utterance" | "vehicle_event" | "derived";
  label: string;
  source: string;
  stationary?: boolean;
  used_by: string[];
}

export interface SignalCatalog {
  source: string;
  version: string;
  status: string;
  domains: { id: string; name: string }[];
  responses: { type: string; label: string; rule: string }[];
  signals: Signal[];
  triggers: Trigger[];
}

export interface ProposalBody {
  id: string;
  title: string;
  statement: string;
  rationale: string;
  source: string;
  category: string;
  priority: string;
  preliminary_asil: string;
  asil_note: string;
  cognitive_capability: string[];
  standard_references: string[];
  verification_method: string;
  acceptance_criteria: string;
  scenario: Scenario | null;
  change_note: string;
}

export interface RunMetrics {
  provider?: string;
  model?: string;
  turns?: number;
  input_tokens?: number;
  output_tokens?: number;
  latency_ms?: number;
  specified_cognitive_level?: string;
  [k: string]: unknown;
}

export interface Run {
  run_id: string;
  agent_id: string;
  mode: string;
  status: RunStatus;
  started: string | null;
  finished: string | null;
  summary: string;
  result: { findings: Finding[]; proposals: ProposalBody[]; metrics: RunMetrics } | null;
}

export interface Agent {
  id: string;
  name: string;
  stage: string;
  description: string;
  depends_on: string[];
  tools: string[];
  publishes: boolean;
  mode: string;
  latest_run: Run | null;
}

export interface Requirement extends ProposalBody {
  version: number;
  state: ReqState;
  updated_at: string;
  updated_by: string;
}

export interface InboxItem {
  pk: number;
  run_id: string;
  agent_id: string;
  status: string;
  proposal: ProposalBody;
}

export interface Overview {
  requirements: number;
  by_state: Record<string, number>;
  by_category: Record<string, number>;
  inbox: number;
  target_cognitive_level: string;
  specified_cognitive_level: string;
  gate: (RunMetrics & { findings: number; by_severity?: Record<string, number>; uncovered?: string[] }) | null;
  cycle_running: boolean;
  runs: number;
  tokens: number;
}

export interface Runtime {
  provider: string;
  model: string;
  max_turns: number;
}

export interface Capability {
  id: string;
  faculty: string;
  title: string;
  level: string;
  covered: boolean;
  requirement_ids: string[];
}

export interface RunEvent {
  seq: number;
  ts: string;
  type: "start" | "turn" | "thinking" | "message" | "tool_call" | "tool_result" | "result" | "error" | "cancelled";
  data: Record<string, any>;
}

export interface Prompt {
  system: string;
  tools: { name: string; description: string; input_schema: unknown }[];
}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, { headers: { "Content-Type": "application/json" }, ...init });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail ?? detail;
    } catch {
      /* non-JSON error body */
    }
    throw new Error(detail);
  }
  return res.json();
}

const post = <T,>(path: string, body?: unknown) =>
  call<T>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) });

export const api = {
  overview: () => call<Overview>("/api/overview"),
  runtime: () => call<Runtime>("/api/runtime"),
  agents: () => call<Agent[]>("/api/agents"),
  prompt: (id: string) => call<Prompt>(`/api/agents/${id}/prompt`),
  startAgent: (id: string) => post<{ run_id: string }>(`/api/agents/${id}/runs`),
  startPipeline: () => post("/api/pipeline/runs"),
  runs: () => call<Run[]>("/api/runs"),
  run: (id: string) => call<Run>(`/api/runs/${id}`),
  events: (id: string, after = 0) => call<RunEvent[]>(`/api/runs/${id}/events?after=${after}`),
  cancel: (id: string) => post(`/api/runs/${id}/cancel`),
  requirements: () => call<Requirement[]>("/api/requirements"),
  history: (id: string) => call<Requirement[]>(`/api/requirements/${id}/history`),
  inbox: () => call<InboxItem[]>("/api/proposals"),
  findings: () => call<Record<string, Finding & { agent_id: string; run_id: string }>>("/api/findings"),
  accept: (pk: number, state: string, edits?: Partial<ProposalBody>) =>
    post(`/api/proposals/${pk}/accept`, { state, edits }),
  reject: (pk: number) => post(`/api/proposals/${pk}/reject`),
  bulk: (pks: number[], action: "accept" | "reject", state = "Draft") =>
    post<{ done: number; errors: string[] }>("/api/proposals/bulk", { pks, action, state }),
  signals: () => call<SignalCatalog>("/api/signals"),
  cognition: () => call<{ target: string; specified: string; capabilities: Capability[] }>("/api/cognition"),
};
