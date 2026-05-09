import type {
  FundAIResponse,
  FundSearchResult,
  FundSentimentResponse,
  FundSummary,
  GroupAIResponse,
  GroupAnalysis,
  GroupSentimentResponse,
  SavedFundGroup,
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8128";

export async function fetchHealth(): Promise<{ status: string; service: string }> {
  return getJson("/api/health");
}

export async function fetchFundSummary(code: string): Promise<FundSummary> {
  return getJson(`/api/funds/${encodeURIComponent(code)}/summary`);
}

export async function searchFunds(keyword: string): Promise<FundSearchResult[]> {
  return getJson(`/api/funds/search?q=${encodeURIComponent(keyword)}`);
}

export async function analyzeGroup(name: string, codes: string[]): Promise<GroupAnalysis> {
  return postJson("/api/groups/analyze", { name, codes });
}

export async function fetchSavedGroups(): Promise<SavedFundGroup[]> {
  return getJson("/api/groups/saved");
}

export async function createSavedGroup(name: string, codes: string[]): Promise<SavedFundGroup> {
  return postJson("/api/groups/saved", { name, codes });
}

export async function updateSavedGroup(id: string, name: string, codes: string[]): Promise<SavedFundGroup> {
  return putJson(`/api/groups/saved/${encodeURIComponent(id)}`, { name, codes });
}

export async function deleteSavedGroup(id: string): Promise<{ deleted: boolean }> {
  const response = await fetch(`${API_BASE}/api/groups/saved/${encodeURIComponent(id)}`, {
    method: "DELETE",
  });
  return handleJson<{ deleted: boolean }>(response);
}

export async function analyzeFundAI(code: string): Promise<FundAIResponse> {
  return postJson("/api/analyze/fund", { code });
}

export async function analyzeGroupAI(name: string, codes: string[]): Promise<GroupAIResponse> {
  return postJson("/api/analyze/group", { name, codes });
}

export async function analyzeFundSentiment(code: string): Promise<FundSentimentResponse> {
  return postJson("/api/sentiment/fund", { code });
}

export async function analyzeGroupSentiment(name: string, codes: string[]): Promise<GroupSentimentResponse> {
  return postJson("/api/sentiment/group", { name, codes });
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

async function putJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "PUT",
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
