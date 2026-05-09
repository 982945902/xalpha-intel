import type { FundSummary, GroupAnalysis } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8128";

export async function fetchHealth(): Promise<{ status: string; service: string }> {
  return getJson("/api/health");
}

export async function fetchFundSummary(code: string): Promise<FundSummary> {
  return getJson(`/api/funds/${encodeURIComponent(code)}/summary`);
}

export async function analyzeGroup(name: string, codes: string[]): Promise<GroupAnalysis> {
  return postJson("/api/groups/analyze", { name, codes });
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`);
  return handleJson<T>(response);
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return handleJson<T>(response);
}

async function handleJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail ?? `Request failed with ${response.status}`);
  }
  return response.json() as Promise<T>;
}
