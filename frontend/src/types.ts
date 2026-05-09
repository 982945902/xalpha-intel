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
