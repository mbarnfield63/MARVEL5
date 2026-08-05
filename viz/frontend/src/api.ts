// API client for the marvel5 viz backend (src/marvel5/viz/api.py).
const BASE_URL = "http://127.0.0.1:8000";

export interface Level {
  level_id: string;
  energy: number;
  uncertainty: number;
  consistency_flag: boolean;
  n_transitions: number;
  network_id: number;
  unverified: boolean;
}

export interface Transition {
  transition_id: string;
  iso: string;
  tag: string;
  freq: number;
  upper: string;
  lower: string;
  upper_qn: string;
  lower_qn: string;
  orig_unc: number | null;
  removed: boolean;
  removed_reason: string | null;
  uncertainty_used: number | null;
  uncertainty_altered: boolean;
  uncertainty_source: string;
  consistency_flag: boolean;
  residual: number | null;
  unverified: boolean;
}

export interface ProjectSummary {
  run_name: string;
  n_levels: number;
  n_transitions: number;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${init?.method ?? "GET"} ${path} failed: ${res.status} ${body}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  loadProject: (path: string, bootstrap_iterations = 100, cutoff = 10.0) =>
    request<ProjectSummary>("/project/load", {
      method: "POST",
      body: JSON.stringify({ path, bootstrap_iterations, cutoff }),
    }),
  getLevels: () => request<Level[]>("/project/levels"),
  getTransitions: () => request<Transition[]>("/project/transitions"),
  removeTransition: (transitionId: string) =>
    request<{ ok: true }>(`/project/transitions/${encodeURIComponent(transitionId)}/remove`, {
      method: "POST",
    }),
  setUncertainty: (transitionId: string, value: number) =>
    request<{ ok: true }>(`/project/transitions/${encodeURIComponent(transitionId)}/uncertainty`, {
      method: "POST",
      body: JSON.stringify({ value }),
    }),
  rerun: (bootstrap_iterations = 100, cutoff = 10.0) =>
    request<ProjectSummary>("/project/rerun", {
      method: "POST",
      body: JSON.stringify({ bootstrap_iterations, cutoff }),
    }),
  exportProject: (output_dir: string) =>
    request<{ ok: true; output_dir: string }>("/project/export", {
      method: "POST",
      body: JSON.stringify({ output_dir }),
    }),
};
