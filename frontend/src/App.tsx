import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  FolderOpen,
  Layers3,
  Newspaper,
  Plus,
  RefreshCw,
  Save,
  Search,
  Sparkles,
  Trash2,
} from "lucide-react";
import {
  analyzeFundAI,
  analyzeFundSentiment,
  analyzeGroup,
  analyzeGroupAI,
  analyzeGroupSentiment,
  createSavedGroup,
  deleteSavedGroup,
  fetchFundSummary,
  fetchHealth,
  fetchSavedGroups,
  searchFunds,
  updateSavedGroup,
} from "./api";
import type {
  AIAnalysis,
  FundPoint,
  FundSearchResult,
  FundSummary,
  GroupAnalysis,
  RiskLevel,
  SavedFundGroup,
  SentimentReport,
  SentimentStance,
  SentimentTone,
} from "./types";

const DEFAULT_GROUP = "501018, 161129";

export function App() {
  const [health, setHealth] = useState("checking");
  const [fundCode, setFundCode] = useState("501018");
  const [fundKeyword, setFundKeyword] = useState("原油");
  const [fundSearchResults, setFundSearchResults] = useState<FundSearchResult[]>([]);
  const [fund, setFund] = useState<FundSummary | null>(null);
  const [fundAI, setFundAI] = useState<AIAnalysis | null>(null);
  const [fundSentiment, setFundSentiment] = useState<SentimentReport | null>(null);
  const [groupName, setGroupName] = useState("原油观察组");
  const [groupCodes, setGroupCodes] = useState(DEFAULT_GROUP);
  const [group, setGroup] = useState<GroupAnalysis | null>(null);
  const [groupAI, setGroupAI] = useState<AIAnalysis | null>(null);
  const [groupSentiment, setGroupSentiment] = useState<SentimentReport | null>(null);
  const [savedGroups, setSavedGroups] = useState<SavedFundGroup[]>([]);
  const [activeSavedGroupId, setActiveSavedGroupId] = useState<string | null>(null);
  const [loadingFund, setLoadingFund] = useState(false);
  const [loadingSearch, setLoadingSearch] = useState(false);
  const [loadingGroup, setLoadingGroup] = useState(false);
  const [loadingFundAI, setLoadingFundAI] = useState(false);
  const [loadingGroupAI, setLoadingGroupAI] = useState(false);
  const [loadingFundSentiment, setLoadingFundSentiment] = useState(false);
  const [loadingGroupSentiment, setLoadingGroupSentiment] = useState(false);
  const [loadingSavedGroups, setLoadingSavedGroups] = useState(false);
  const [savingGroup, setSavingGroup] = useState(false);
  const [deletingGroup, setDeletingGroup] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchHealth()
      .then((result) => setHealth(result.status))
      .catch(() => setHealth("offline"));
    void loadSavedGroups();
  }, []);

  async function loadFund(code = fundCode) {
    const normalized = code.trim();
    if (!normalized) return;
    setLoadingFund(true);
    setError(null);
    try {
      const result = await fetchFundSummary(normalized);
      setFund(result);
      setFundAI(null);
      setFundSentiment(null);
      setFundCode(normalized);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "基金查询失败");
    } finally {
      setLoadingFund(false);
    }
  }

  async function searchFundCodes() {
    const keyword = fundKeyword.trim();
    if (!keyword) return;
    setLoadingSearch(true);
    setError(null);
    try {
      const results = await searchFunds(keyword);
      setFundSearchResults(results);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "基金搜索失败");
    } finally {
      setLoadingSearch(false);
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
      setGroupAI(null);
      setGroupSentiment(null);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "组合分析失败");
    } finally {
      setLoadingGroup(false);
    }
  }

  async function loadFundAI() {
    const normalized = fundCode.trim();
    if (!normalized) return;
    setLoadingFundAI(true);
    setError(null);
    try {
      const result = await analyzeFundAI(normalized);
      setFund(result.summary);
      setFundAI(result.analysis);
      setFundSentiment(null);
      setFundCode(normalized);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "AI 分析失败");
    } finally {
      setLoadingFundAI(false);
    }
  }

  async function loadGroupAI() {
    const codes = parseCodes(groupCodes);
    if (codes.length === 0) return;
    setLoadingGroupAI(true);
    setError(null);
    try {
      const result = await analyzeGroupAI(groupName.trim() || "fund group", codes);
      setGroup(result.group);
      setGroupAI(result.analysis);
      setGroupSentiment(null);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "AI 组合分析失败");
    } finally {
      setLoadingGroupAI(false);
    }
  }

  async function loadFundSentiment() {
    const normalized = fundCode.trim();
    if (!normalized) return;
    setLoadingFundSentiment(true);
    setError(null);
    try {
      const result = await analyzeFundSentiment(normalized);
      setFund(result.summary);
      setFundSentiment(result.sentiment);
      setFundCode(normalized);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "基金舆情分析失败");
    } finally {
      setLoadingFundSentiment(false);
    }
  }

  async function loadGroupSentiment() {
    const codes = parseCodes(groupCodes);
    if (codes.length === 0) return;
    setLoadingGroupSentiment(true);
    setError(null);
    try {
      const result = await analyzeGroupSentiment(groupName.trim() || "fund group", codes);
      setGroup(result.group);
      setGroupSentiment(result.sentiment);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "基金组舆情分析失败");
    } finally {
      setLoadingGroupSentiment(false);
    }
  }

  async function loadSavedGroups() {
    setLoadingSavedGroups(true);
    setError(null);
    try {
      setSavedGroups(await fetchSavedGroups());
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "保存组加载失败");
    } finally {
      setLoadingSavedGroups(false);
    }
  }

  async function saveNewGroup() {
    const codes = parseCodes(groupCodes);
    if (codes.length === 0) return;
    setSavingGroup(true);
    setError(null);
    try {
      const saved = await createSavedGroup(groupName.trim() || "fund group", codes);
      setActiveSavedGroupId(saved.id);
      setSavedGroups(await fetchSavedGroups());
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "保存基金组失败");
    } finally {
      setSavingGroup(false);
    }
  }

  async function updateCurrentSavedGroup() {
    const codes = parseCodes(groupCodes);
    if (!activeSavedGroupId || codes.length === 0) return;
    setSavingGroup(true);
    setError(null);
    try {
      const saved = await updateSavedGroup(activeSavedGroupId, groupName.trim() || "fund group", codes);
      setActiveSavedGroupId(saved.id);
      setSavedGroups(await fetchSavedGroups());
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "更新基金组失败");
    } finally {
      setSavingGroup(false);
    }
  }

  async function deleteCurrentSavedGroup() {
    if (!activeSavedGroupId) return;
    setDeletingGroup(true);
    setError(null);
    try {
      await deleteSavedGroup(activeSavedGroupId);
      setActiveSavedGroupId(null);
      setSavedGroups(await fetchSavedGroups());
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "删除基金组失败");
    } finally {
      setDeletingGroup(false);
    }
  }

  function pickSavedGroup(saved: SavedFundGroup) {
    setActiveSavedGroupId(saved.id);
    setGroupName(saved.name);
    setGroupCodes(saved.codes.join(", "));
    setGroup(null);
    setGroupAI(null);
    setGroupSentiment(null);
  }

  function appendCodeToGroup(code: string) {
    const codes = parseCodes(groupCodes);
    if (!codes.includes(code)) {
      setGroupCodes([...codes, code].join(", "));
      setActiveSavedGroupId(null);
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
            className="search-box"
            onSubmit={(event) => {
              event.preventDefault();
              void searchFundCodes();
            }}
          >
            <label>
              <span>按基金名找代码</span>
              <div className="query-row compact">
                <input
                  value={fundKeyword}
                  onChange={(event) => setFundKeyword(event.target.value)}
                  placeholder="输入关键词，如 原油、纳指、沪深300"
                />
                <button type="submit" disabled={loadingSearch} title="搜索基金代码">
                  {loadingSearch ? <RefreshCw size={18} className="spin" /> : <Search size={18} />}
                  <span>找代码</span>
                </button>
              </div>
            </label>
            {fundSearchResults.length > 0 ? (
              <div className="search-results">
                {fundSearchResults.map((result) => (
                  <div className="search-result" key={result.code}>
                    <div>
                      <strong>{result.code}</strong>
                      <span>{result.name}</span>
                      <small>{[result.fund_type, result.company, result.latest_date].filter(Boolean).join(" · ")}</small>
                    </div>
                    <div className="result-actions">
                      <button type="button" onClick={() => void loadFund(result.code)} title="查询这只基金">
                        <Search size={16} />
                      </button>
                      <button type="button" onClick={() => appendCodeToGroup(result.code)} title="加入基金组">
                        <Plus size={16} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : null}
          </form>

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

          <button
            className="secondary-action"
            onClick={() => void loadFundAI()}
            disabled={loadingFundAI || loadingFund}
            title="生成基金 AI 分析"
          >
            {loadingFundAI ? <RefreshCw size={18} className="spin" /> : <Sparkles size={18} />}
            <span>AI 分析基金</span>
          </button>

          <button
            className="secondary-action"
            onClick={() => void loadFundSentiment()}
            disabled={loadingFundSentiment || loadingFund}
            title="生成基金综合舆情"
          >
            {loadingFundSentiment ? <RefreshCw size={18} className="spin" /> : <Newspaper size={18} />}
            <span>综合舆情</span>
          </button>

          {fund ? <FundPanel fund={fund} /> : <EmptyState text="输入基金代码后查看净值、回撤、波动与走势。" />}
          {fundAI ? <AIInsight analysis={fundAI} /> : null}
          {fundSentiment ? <SentimentPanel report={fundSentiment} /> : null}
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
            <SavedGroupsPanel
              groups={savedGroups}
              activeId={activeSavedGroupId}
              loading={loadingSavedGroups}
              onPick={pickSavedGroup}
              onReload={() => void loadSavedGroups()}
            />
            <label>
              <span>组名</span>
              <input
                value={groupName}
                onChange={(event) => {
                  setGroupName(event.target.value);
                  setGroupAI(null);
                  setGroupSentiment(null);
                }}
              />
            </label>
            <label>
              <span>基金代码</span>
              <textarea
                value={groupCodes}
                onChange={(event) => {
                  setGroupCodes(event.target.value);
                  setGroupAI(null);
                  setGroupSentiment(null);
                }}
                placeholder="多个代码用逗号、空格或换行分隔"
              />
            </label>
            <div className="group-save-actions">
              <button
                type="button"
                className="secondary-action"
                onClick={() => void saveNewGroup()}
                disabled={savingGroup}
                title="保存为新基金组"
              >
                {savingGroup ? <RefreshCw size={18} className="spin" /> : <Save size={18} />}
                <span>保存新组</span>
              </button>
              <button
                type="button"
                className="secondary-action"
                onClick={() => void updateCurrentSavedGroup()}
                disabled={savingGroup || !activeSavedGroupId}
                title="更新当前已保存组"
              >
                {savingGroup ? <RefreshCw size={18} className="spin" /> : <Save size={18} />}
                <span>更新当前组</span>
              </button>
              <button
                type="button"
                className="danger-action"
                onClick={() => void deleteCurrentSavedGroup()}
                disabled={deletingGroup || !activeSavedGroupId}
                title="删除当前已保存组"
              >
                {deletingGroup ? <RefreshCw size={18} className="spin" /> : <Trash2 size={18} />}
                <span>删除</span>
              </button>
            </div>
            <button onClick={() => void loadGroup()} disabled={loadingGroup} title="分析基金组">
              {loadingGroup ? <RefreshCw size={18} className="spin" /> : <Layers3 size={18} />}
              <span>分析这一组</span>
            </button>
            <button
              className="secondary-action"
              onClick={() => void loadGroupAI()}
              disabled={loadingGroupAI || loadingGroup}
              title="生成基金组 AI 分析"
            >
              {loadingGroupAI ? <RefreshCw size={18} className="spin" /> : <Sparkles size={18} />}
              <span>AI 分析这一组</span>
            </button>
            <button
              className="secondary-action"
              onClick={() => void loadGroupSentiment()}
              disabled={loadingGroupSentiment || loadingGroup}
              title="生成基金组综合舆情"
            >
              {loadingGroupSentiment ? <RefreshCw size={18} className="spin" /> : <Newspaper size={18} />}
              <span>综合舆情</span>
            </button>
          </div>

          {group ? <GroupPanel group={group} onPick={(code) => void loadFund(code)} /> : <EmptyState text="输入多个基金代码，形成一个观察组并比较收益、回撤和风险。" />}
          {groupAI ? <AIInsight analysis={groupAI} /> : null}
          {groupSentiment ? <SentimentPanel report={groupSentiment} /> : null}
        </section>
      </section>
    </main>
  );
}

function SavedGroupsPanel({
  groups,
  activeId,
  loading,
  onPick,
  onReload,
}: {
  groups: SavedFundGroup[];
  activeId: string | null;
  loading: boolean;
  onPick: (group: SavedFundGroup) => void;
  onReload: () => void;
}) {
  return (
    <section className="saved-groups">
      <div className="saved-groups-head">
        <div>
          <div className="section-kicker">Saved Groups</div>
          <h3>已保存组</h3>
        </div>
        <button type="button" onClick={onReload} disabled={loading} title="刷新保存组">
          {loading ? <RefreshCw size={16} className="spin" /> : <RefreshCw size={16} />}
        </button>
      </div>
      {groups.length > 0 ? (
        <div className="saved-group-list">
          {groups.map((group) => (
            <button
              type="button"
              className={`saved-group-item${group.id === activeId ? " saved-group-active" : ""}`}
              key={group.id}
              onClick={() => onPick(group)}
              title="载入这个基金组"
            >
              <FolderOpen size={16} />
              <span>
                <strong>{group.name}</strong>
                <small>{group.codes.join(", ")}</small>
              </span>
            </button>
          ))}
        </div>
      ) : (
        <div className="saved-group-empty">暂无保存组</div>
      )}
    </section>
  );
}

function AIInsight({ analysis }: { analysis: AIAnalysis }) {
  return (
    <section className="ai-insight">
      <div className="ai-head">
        <div>
          <div className="section-kicker">AI Insight</div>
          <h3>{analysis.headline}</h3>
        </div>
        <span className={`source source-${analysis.source}`}>{analysis.source.toUpperCase()}</span>
      </div>
      <ul>
        {analysis.bullets.map((bullet) => (
          <li key={bullet}>{bullet}</li>
        ))}
      </ul>
      <p>{analysis.disclaimer}</p>
    </section>
  );
}

function SentimentPanel({ report }: { report: SentimentReport }) {
  return (
    <section className="sentiment-panel">
      <div className="sentiment-head">
        <div>
          <div className="section-kicker">Sentiment</div>
          <h3>{report.subject}</h3>
        </div>
        <span className={`stance stance-${report.stance}`}>{stanceLabel(report.stance)}</span>
      </div>

      <div className="sentiment-counts">
        <Metric label="舆情分" value={report.score.toFixed(2)} tone={toneForStance(report.stance)} />
        <Metric label="利好" value={String(report.bullish_count)} tone="good" />
        <Metric label="利空" value={String(report.bearish_count)} tone="bad" />
        <Metric label="中性" value={String(report.neutral_count)} />
      </div>

      <p className="sentiment-summary">{report.summary}</p>

      <div className="keyword-row">
        {report.keywords.map((keyword) => (
          <span key={keyword}>{keyword}</span>
        ))}
      </div>

      <div className="sentiment-list">
        {report.items.length > 0 ? (
          report.items.map((item) => <SentimentRow key={`${item.title}-${item.url}`} item={item} />)
        ) : (
          <div className="sentiment-empty">暂无可用舆情材料</div>
        )}
      </div>

      <p className="sentiment-disclaimer">
        {report.analysis_source.toUpperCase()} · {report.disclaimer}
      </p>
    </section>
  );
}

function SentimentRow({ item }: { item: SentimentReport["items"][number] }) {
  const title = item.url ? (
    <a href={item.url} target="_blank" rel="noreferrer">
      {item.title}
    </a>
  ) : (
    <span>{item.title}</span>
  );

  return (
    <article className="sentiment-item">
      <div className="sentiment-item-head">
        <span className={`tone-badge tone-badge-${item.tone}`}>{toneLabel(item.tone)}</span>
        <small>{[item.source, item.published_at].filter(Boolean).join(" · ")}</small>
      </div>
      <strong>{title}</strong>
      <p>{item.reason}</p>
    </article>
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

function toneForStance(stance: SentimentStance): string {
  if (stance === "bullish") return "good";
  if (stance === "bearish") return "bad";
  if (stance === "mixed") return "warn";
  return "neutral";
}

function stanceLabel(stance: SentimentStance): string {
  const labels: Record<SentimentStance, string> = {
    bullish: "偏利好",
    bearish: "偏利空",
    mixed: "多空分歧",
    neutral: "中性",
    insufficient: "材料不足",
  };
  return labels[stance];
}

function toneLabel(tone: SentimentTone): string {
  const labels: Record<SentimentTone, string> = {
    bullish: "利好",
    bearish: "利空",
    neutral: "中性",
  };
  return labels[tone];
}
