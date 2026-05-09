import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  Layers3,
  RefreshCw,
  Search,
} from "lucide-react";
import { analyzeGroup, fetchFundSummary, fetchHealth } from "./api";
import type { FundPoint, FundSummary, GroupAnalysis, RiskLevel } from "./types";

const DEFAULT_GROUP = "501018, 161129";

export function App() {
  const [health, setHealth] = useState("checking");
  const [fundCode, setFundCode] = useState("501018");
  const [fund, setFund] = useState<FundSummary | null>(null);
  const [groupName, setGroupName] = useState("原油观察组");
  const [groupCodes, setGroupCodes] = useState(DEFAULT_GROUP);
  const [group, setGroup] = useState<GroupAnalysis | null>(null);
  const [loadingFund, setLoadingFund] = useState(false);
  const [loadingGroup, setLoadingGroup] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchHealth()
      .then((result) => setHealth(result.status))
      .catch(() => setHealth("offline"));
  }, []);

  async function loadFund(code = fundCode) {
    const normalized = code.trim();
    if (!normalized) return;
    setLoadingFund(true);
    setError(null);
    try {
      const result = await fetchFundSummary(normalized);
      setFund(result);
      setFundCode(normalized);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "基金查询失败");
    } finally {
      setLoadingFund(false);
    }
  }

  async function loadGroup() {
    const codes = parseCodes(groupCodes);
    if (codes.length === 0) return;
    setLoadingGroup(true);
    setError(null);
    try {
      const result = await analyzeGroup(groupName.trim() || "fund group", codes);
      setGroup(result);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "组合分析失败");
    } finally {
      setLoadingGroup(false);
    }
  }

  const dashboardStats = useMemo(() => {
    if (!group) {
      return [
        { label: "Data Source", value: health.toUpperCase(), tone: health === "ok" ? "good" : "warn" },
        { label: "Group Funds", value: "--", tone: "neutral" },
        { label: "Avg Return", value: "--", tone: "neutral" },
        { label: "Worst DD", value: "--", tone: "neutral" },
      ];
    }
    return [
      { label: "Data Source", value: health.toUpperCase(), tone: health === "ok" ? "good" : "warn" },
      { label: "Group Funds", value: String(group.member_count), tone: "neutral" },
      { label: "Avg Return", value: formatPct(group.average_return), tone: toneForReturn(group.average_return) },
      { label: "Worst DD", value: formatPct(group.worst_drawdown), tone: "bad" },
    ];
  }, [group, health]);

  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <div className="eyebrow">xalpha intel</div>
          <h1>投资情报台</h1>
        </div>
        <div className={`status status-${health === "ok" ? "good" : "warn"}`}>
          <Activity size={16} />
          <span>{health === "ok" ? "Backend Online" : "Backend Checking"}</span>
        </div>
      </header>

      {error ? (
        <div className="alert">
          <AlertTriangle size={18} />
          <span>{error}</span>
        </div>
      ) : null}

      <section className="metric-grid">
        {dashboardStats.map((item) => (
          <div className="metric-card" key={item.label}>
            <span>{item.label}</span>
            <strong className={`tone-${item.tone}`}>{item.value}</strong>
          </div>
        ))}
      </section>

      <section className="workspace-grid">
        <section className="panel">
          <div className="panel-head">
            <div>
              <div className="section-kicker">Single Fund</div>
              <h2>基金工具台</h2>
            </div>
            <BarChart3 size={22} />
          </div>

          <form
            className="query-row"
            onSubmit={(event) => {
              event.preventDefault();
              void loadFund();
            }}
          >
            <input
              value={fundCode}
              onChange={(event) => setFundCode(event.target.value)}
              placeholder="输入基金代码，如 501018"
            />
            <button type="submit" disabled={loadingFund} title="查询基金">
              {loadingFund ? <RefreshCw size={18} className="spin" /> : <Search size={18} />}
              <span>查询</span>
            </button>
          </form>

          {fund ? <FundPanel fund={fund} /> : <EmptyState text="输入基金代码后查看净值、回撤、波动与走势。" />}
        </section>

        <section className="panel">
          <div className="panel-head">
            <div>
              <div className="section-kicker">Group</div>
              <h2>基金组分析</h2>
            </div>
            <Layers3 size={22} />
          </div>

          <div className="group-form">
            <label>
              <span>组名</span>
              <input value={groupName} onChange={(event) => setGroupName(event.target.value)} />
            </label>
            <label>
              <span>基金代码</span>
              <textarea
                value={groupCodes}
                onChange={(event) => setGroupCodes(event.target.value)}
                placeholder="多个代码用逗号、空格或换行分隔"
              />
            </label>
            <button onClick={() => void loadGroup()} disabled={loadingGroup} title="分析基金组">
              {loadingGroup ? <RefreshCw size={18} className="spin" /> : <Layers3 size={18} />}
              <span>分析这一组</span>
            </button>
          </div>

          {group ? <GroupPanel group={group} onPick={(code) => void loadFund(code)} /> : <EmptyState text="输入多个基金代码，形成一个观察组并比较收益、回撤和风险。" />}
        </section>
      </section>
    </main>
  );
}

function FundPanel({ fund }: { fund: FundSummary }) {
  return (
    <div className="fund-detail">
      <div className="fund-title">
        <div>
          <h3>{fund.name}</h3>
          <span>{fund.code} · {fund.latest_date ?? "--"}</span>
        </div>
        <RiskBadge level={fund.risk_level} />
      </div>

      <Sparkline points={fund.points} />

      <div className="detail-grid">
        <Metric label="最新净值" value={fund.latest_net_value.toFixed(4)} />
        <Metric label="区间收益" value={formatPct(fund.total_return)} tone={toneForReturn(fund.total_return)} />
        <Metric label="最大回撤" value={formatPct(fund.max_drawdown)} tone="bad" />
        <Metric label="年化波动" value={formatPct(fund.annualized_volatility)} />
      </div>
    </div>
  );
}

function GroupPanel({ group, onPick }: { group: GroupAnalysis; onPick: (code: string) => void }) {
  return (
    <div className="group-result">
      <div className="group-summary">
        <div>
          <h3>{group.name}</h3>
          <p>{group.narrative}</p>
        </div>
        <RiskBadge level={group.risk_level} />
      </div>

      <div className="leader-row">
        <Metric label="最强" value={`${group.best_member.code} ${formatPct(group.best_member.total_return)}`} tone="good" />
        <Metric label="最弱" value={`${group.weakest_member.code} ${formatPct(group.weakest_member.total_return)}`} tone="bad" />
      </div>

      <div className="table">
        <div className="table-row table-head">
          <span>代码</span>
          <span>名称</span>
          <span>收益</span>
          <span>回撤</span>
          <span>风险</span>
        </div>
        {group.members.map((member) => (
          <button className="table-row table-button" key={member.code} onClick={() => onPick(member.code)}>
            <span>{member.code}</span>
            <span>{member.name}</span>
            <span className={toneForReturn(member.total_return)}>{formatPct(member.total_return)}</span>
            <span className="bad">{formatPct(member.max_drawdown)}</span>
            <span><RiskBadge level={member.risk_level} compact /></span>
          </button>
        ))}
      </div>
    </div>
  );
}

function Metric({ label, value, tone = "neutral" }: { label: string; value: string; tone?: string }) {
  return (
    <div className="mini-metric">
      <span>{label}</span>
      <strong className={`tone-${tone}`}>{value}</strong>
    </div>
  );
}

function RiskBadge({ level, compact = false }: { level: RiskLevel; compact?: boolean }) {
  return <span className={`risk risk-${level}`}>{compact ? level.toUpperCase() : `Risk ${level.toUpperCase()}`}</span>;
}

function EmptyState({ text }: { text: string }) {
  return <div className="empty-state">{text}</div>;
}

function Sparkline({ points }: { points: FundPoint[] }) {
  const values = points.map((point) => point.net_value);
  if (values.length < 2) {
    return <div className="sparkline-empty">数据点不足</div>;
  }

  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const path = values
    .map((value, index) => {
      const x = (index / (values.length - 1)) * 100;
      const y = 56 - ((value - min) / range) * 48;
      return `${index === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`;
    })
    .join(" ");

  return (
    <svg className="sparkline" viewBox="0 0 100 64" role="img" aria-label="基金净值走势">
      <path d={path} />
    </svg>
  );
}

function parseCodes(value: string): string[] {
  return Array.from(
    new Set(
      value
        .split(/[\s,，;；]+/)
        .map((code) => code.trim())
        .filter(Boolean),
    ),
  );
}

function formatPct(value: number): string {
  return `${(value * 100).toFixed(2)}%`;
}

function toneForReturn(value: number): string {
  if (value > 0) return "good";
  if (value < 0) return "bad";
  return "neutral";
}
