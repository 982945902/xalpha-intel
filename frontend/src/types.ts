export type RiskLevel = "low" | "medium" | "high";

export type FundPoint = {
  date: string;
  net_value: number;
};

export type FundSummary = {
  code: string;
  name: string;
  latest_date: string | null;
  latest_net_value: number;
  total_return: number;
  max_drawdown: number;
  annualized_volatility: number;
  observation_count: number;
  risk_level: RiskLevel;
  points: FundPoint[];
};

export type FundSearchResult = {
  code: string;
  name: string;
  pinyin: string | null;
  category: string | null;
  company: string | null;
  fund_type: string | null;
  latest_net_value: number | null;
  latest_date: string | null;
};

export type GroupAnalysis = {
  name: string;
  member_count: number;
  members: FundSummary[];
  best_member: FundSummary;
  weakest_member: FundSummary;
  average_return: number;
  worst_drawdown: number;
  risk_level: RiskLevel;
  narrative: string;
};

export type SavedFundGroup = {
  id: string;
  name: string;
  codes: string[];
  created_at: string;
  updated_at: string;
};

export type AIAnalysis = {
  source: "codex" | "rules";
  headline: string;
  bullets: string[];
  disclaimer: string;
};

export type SentimentTone = "bullish" | "bearish" | "neutral";

export type SentimentStance = "bullish" | "bearish" | "mixed" | "neutral" | "insufficient";

export type SentimentItem = {
  title: string;
  source: string;
  published_at: string | null;
  url: string | null;
  tone: SentimentTone;
  confidence: number;
  reason: string;
  matched_terms: string[];
};

export type SentimentReport = {
  subject_type: "fund" | "group";
  subject: string;
  stance: SentimentStance;
  score: number;
  bullish_count: number;
  bearish_count: number;
  neutral_count: number;
  keywords: string[];
  items: SentimentItem[];
  summary: string;
  analysis_source: "codex" | "rules";
  disclaimer: string;
};

export type FundAIResponse = {
  summary: FundSummary;
  analysis: AIAnalysis;
};

export type GroupAIResponse = {
  group: GroupAnalysis;
  analysis: AIAnalysis;
};

export type FundSentimentResponse = {
  summary: FundSummary;
  sentiment: SentimentReport;
};

export type GroupSentimentResponse = {
  group: GroupAnalysis;
  sentiment: SentimentReport;
};
