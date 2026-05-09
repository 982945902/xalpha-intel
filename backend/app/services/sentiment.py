from __future__ import annotations

from dataclasses import dataclass
from html import unescape
import os
import re
from typing import Callable
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from backend.app.services.ai_analysis import DISCLAIMER, Runner, run_codex
from backend.app.services.metrics import FundSummary

AnnouncementFetcher = Callable[[str, int], list["RawSentimentItem"]]
NewsFetcher = Callable[[str, int], list["RawSentimentItem"]]

MAX_REPORT_ITEMS = 12

BULLISH_TERMS = (
    "上涨",
    "大涨",
    "创新高",
    "减产",
    "库存下降",
    "需求回暖",
    "需求增加",
    "美元走弱",
    "降息",
    "超预期",
    "增长",
    "盈利",
    "批准",
    "净流入",
    "回暖",
    "利好",
    "修复",
    "上调",
    "提振",
)

BEARISH_TERMS = (
    "下跌",
    "大跌",
    "暴跌",
    "风险",
    "溢价风险",
    "暂停申购",
    "限购",
    "亏损",
    "清盘",
    "处罚",
    "监管",
    "下调",
    "低于预期",
    "衰退",
    "库存增加",
    "增产",
    "美元走强",
    "赎回",
    "承压",
    "利空",
)

THEME_KEYWORDS = (
    (("原油", "石油", "油气"), ("原油", "OPEC", "EIA库存", "美元指数")),
    (("黄金", "金价"), ("黄金", "美元指数", "美债收益率")),
    (("纳指", "纳斯达克", "标普", "美股"), ("美股", "纳斯达克", "美联储", "美债收益率")),
    (("半导体", "芯片"), ("半导体", "芯片", "AI芯片")),
    (("医药", "医疗", "创新药"), ("医药", "集采", "创新药")),
    (("新能源", "光伏", "电池", "锂"), ("新能源", "光伏", "锂电池")),
    (("消费", "白酒"), ("消费", "社零", "白酒")),
    (("银行", "金融", "证券"), ("银行", "券商", "利率")),
)


@dataclass(frozen=True)
class RawSentimentItem:
    title: str
    source: str
    published_at: str | None
    url: str | None
    content: str | None = None


@dataclass(frozen=True)
class SentimentItem:
    title: str
    source: str
    published_at: str | None
    url: str | None
    tone: str
    confidence: float
    reason: str
    matched_terms: list[str]


@dataclass(frozen=True)
class SentimentReport:
    subject_type: str
    subject: str
    stance: str
    score: float
    bullish_count: int
    bearish_count: int
    neutral_count: int
    keywords: list[str]
    items: list[SentimentItem]
    summary: str
    analysis_source: str
    disclaimer: str = DISCLAIMER


def analyze_fund_sentiment(
    summary: FundSummary,
    fetch_announcements: AnnouncementFetcher = None,
    fetch_news: NewsFetcher = None,
    runner: Runner | None = None,
) -> SentimentReport:
    announcement_fetcher = fetch_announcements or fetch_fund_announcements
    news_fetcher = fetch_news or fetch_news_by_term
    keywords = infer_fund_keywords(summary)

    raw_items = _safe_fetch_announcements(announcement_fetcher, summary.code, limit=6)
    for keyword in keywords[:4]:
        raw_items.extend(_safe_fetch_news(news_fetcher, keyword, limit=4))

    items = [
        classify_sentiment_item(item)
        for item in _dedupe_raw_items(raw_items)[:MAX_REPORT_ITEMS]
    ]
    return _build_report(
        subject_type="fund",
        subject=f"{summary.code} {summary.name}",
        keywords=keywords,
        items=items,
        runner=runner,
    )


def analyze_group_sentiment(
    name: str,
    members: list[FundSummary],
    fetch_announcements: AnnouncementFetcher = None,
    fetch_news: NewsFetcher = None,
    runner: Runner | None = None,
) -> SentimentReport:
    announcement_fetcher = fetch_announcements or fetch_fund_announcements
    news_fetcher = fetch_news or fetch_news_by_term
    keywords = infer_group_keywords(name, members)

    raw_items: list[RawSentimentItem] = []
    for member in members[:6]:
        raw_items.extend(_safe_fetch_announcements(announcement_fetcher, member.code, limit=3))
    for keyword in keywords[:6]:
        raw_items.extend(_safe_fetch_news(news_fetcher, keyword, limit=3))

    items = [
        classify_sentiment_item(item)
        for item in _dedupe_raw_items(raw_items)[:MAX_REPORT_ITEMS]
    ]
    return _build_report(
        subject_type="group",
        subject=name,
        keywords=keywords,
        items=items,
        runner=runner,
    )


def infer_fund_keywords(summary: FundSummary) -> list[str]:
    text = f"{summary.code} {summary.name}"
    keywords = [summary.name]
    for triggers, terms in THEME_KEYWORDS:
        if any(trigger in text for trigger in triggers):
            keywords.extend(terms)
    return _unique_non_empty(keywords)[:8]


def infer_group_keywords(name: str, members: list[FundSummary]) -> list[str]:
    keywords = [name]
    for member in members:
        keywords.extend(infer_fund_keywords(member))
    return _unique_non_empty(keywords)[:10]


def classify_sentiment_item(raw: RawSentimentItem) -> SentimentItem:
    text = f"{raw.title} {raw.content or ''}"
    bullish_matches = _matched_terms(text, BULLISH_TERMS)
    bearish_matches = _matched_terms(text, BEARISH_TERMS)
    bullish_score = len(bullish_matches)
    bearish_score = len(bearish_matches)

    if bearish_score > bullish_score:
        tone = "bearish"
        winning_terms = bearish_matches
    elif bullish_score > bearish_score:
        tone = "bullish"
        winning_terms = bullish_matches
    else:
        tone = "neutral"
        winning_terms = bullish_matches + bearish_matches

    confidence = _confidence(bullish_score, bearish_score)
    reason = _reason(bullish_matches, bearish_matches)

    return SentimentItem(
        title=raw.title,
        source=raw.source,
        published_at=raw.published_at,
        url=raw.url,
        tone=tone,
        confidence=confidence,
        reason=reason,
        matched_terms=winning_terms,
    )


def fetch_fund_announcements(code: str, limit: int = 6) -> list[RawSentimentItem]:
    try:
        from xalpha.info import FundReport

        report = FundReport(code)
        rows = []
        for type_ in (0, 1, 3):
            try:
                rows.extend(report.show_report_list(type_=type_))
            except Exception:
                continue
    except Exception:
        return []

    rows = sorted(rows, key=lambda row: str(row.get("PUBLISHDATE", "")), reverse=True)
    items: list[RawSentimentItem] = []
    for row in rows[:limit]:
        title = str(row.get("TITLE") or row.get("ShortTitle") or "").strip()
        if not title:
            continue
        report_id = row.get("ID")
        url = (
            "https://np-cnotice-fund.eastmoney.com/api/content/ann?"
            f"client_source=web_fund&show_all=1&art_code={report_id}"
            if report_id
            else f"http://fundf10.eastmoney.com/jjgg_{code}_3.html"
        )
        items.append(
            RawSentimentItem(
                title=title,
                source="东方财富基金公告",
                published_at=_date_part(row.get("PUBLISHDATEDesc") or row.get("PUBLISHDATE")),
                url=url,
                content=str(row.get("ShortTitle") or ""),
            )
        )
    return items


def fetch_news_by_term(term: str, limit: int = 4) -> list[RawSentimentItem]:
    query = urlencode({"q": term, "hl": "zh-CN", "gl": "CN", "ceid": "CN:zh-Hans"})
    url = f"https://news.google.com/rss/search?{query}"
    timeout = float(os.getenv("SENTIMENT_NEWS_TIMEOUT", "6"))
    request = Request(url, headers={"User-Agent": "xalpha-intel/0.1"})

    try:
        with urlopen(request, timeout=timeout) as response:
            payload = response.read()
        root = ET.fromstring(payload)
    except Exception:
        return []

    items: list[RawSentimentItem] = []
    for entry in root.findall("./channel/item")[:limit]:
        title = _clean_html(entry.findtext("title") or "")
        if not title:
            continue
        source_node = entry.find("source")
        source = _clean_html(source_node.text if source_node is not None else "") or "Google News"
        items.append(
            RawSentimentItem(
                title=title,
                source=source,
                published_at=entry.findtext("pubDate"),
                url=entry.findtext("link"),
                content=_clean_html(entry.findtext("description") or ""),
            )
        )
    return items


def _build_report(
    subject_type: str,
    subject: str,
    keywords: list[str],
    items: list[SentimentItem],
    runner: Runner | None,
) -> SentimentReport:
    bullish_count = sum(item.tone == "bullish" for item in items)
    bearish_count = sum(item.tone == "bearish" for item in items)
    neutral_count = sum(item.tone == "neutral" for item in items)
    score = _score(bullish_count, bearish_count, len(items))
    stance = _stance(score, bullish_count, bearish_count, len(items))
    codex_text = _try_runner(_sentiment_prompt(subject, keywords, items, stance), runner)

    return SentimentReport(
        subject_type=subject_type,
        subject=subject,
        stance=stance,
        score=score,
        bullish_count=bullish_count,
        bearish_count=bearish_count,
        neutral_count=neutral_count,
        keywords=keywords,
        items=items,
        summary=codex_text or _rule_summary(stance, bullish_count, bearish_count, neutral_count),
        analysis_source="codex" if codex_text else "rules",
    )


def _sentiment_prompt(
    subject: str,
    keywords: list[str],
    items: list[SentimentItem],
    stance: str,
) -> str:
    lines = "\n".join(
        f"- [{item.tone}] {item.title} ({item.source}, {item.published_at or 'unknown'})"
        for item in items[:10]
    )
    return (
        "你是基金舆情研究助手。基于以下公告和新闻，输出一段 1-3 句中文结论，"
        "说明利好/利空来源、分歧和需要继续观察的变量。不要给直接买卖指令。"
        f"\n对象: {subject}"
        f"\n关键词: {', '.join(keywords)}"
        f"\n规则初判: {stance}"
        f"\n材料:\n{lines or '- 暂无可用材料'}"
    )


def _try_runner(prompt: str, runner: Runner | None) -> str | None:
    active_runner = runner if runner is not None else run_codex
    try:
        text = active_runner(prompt).strip()
    except Exception:
        return None
    if not text:
        return None
    return " ".join(line.strip(" -•\t") for line in text.splitlines() if line.strip())[:320]


def _rule_summary(
    stance: str,
    bullish_count: int,
    bearish_count: int,
    neutral_count: int,
) -> str:
    if stance == "insufficient":
        return "暂未抓到足够的公告或新闻材料，建议稍后重试或补充新闻源。"
    label = {
        "bullish": "偏利好",
        "bearish": "偏利空",
        "mixed": "多空分歧",
        "neutral": "中性",
    }.get(stance, stance)
    return (
        f"规则初判为{label}：利好 {bullish_count} 条，"
        f"利空 {bearish_count} 条，中性 {neutral_count} 条。"
    )


def _score(bullish_count: int, bearish_count: int, item_count: int) -> float:
    if item_count == 0:
        return 0.0
    return round((bullish_count - bearish_count) / item_count, 2)


def _stance(score: float, bullish_count: int, bearish_count: int, item_count: int) -> str:
    if item_count == 0:
        return "insufficient"
    if bullish_count > 0 and bearish_count > 0 and abs(score) < 0.34:
        return "mixed"
    if score >= 0.2:
        return "bullish"
    if score <= -0.2:
        return "bearish"
    return "neutral"


def _confidence(bullish_score: int, bearish_score: int) -> float:
    total = bullish_score + bearish_score
    if total == 0:
        return 0.5
    gap = abs(bullish_score - bearish_score)
    return round(min(0.95, 0.55 + total * 0.08 + gap * 0.12), 2)


def _reason(bullish_matches: list[str], bearish_matches: list[str]) -> str:
    parts = []
    if bullish_matches:
        parts.append(f"命中利好词: {'、'.join(bullish_matches)}")
    if bearish_matches:
        parts.append(f"命中利空词: {'、'.join(bearish_matches)}")
    return "；".join(parts) if parts else "未命中明显利好或利空词，暂按中性处理。"


def _matched_terms(text: str, terms: tuple[str, ...]) -> list[str]:
    return [term for term in terms if term in text]


def _dedupe_raw_items(items: list[RawSentimentItem]) -> list[RawSentimentItem]:
    seen: set[str] = set()
    result: list[RawSentimentItem] = []
    for item in items:
        key = item.title.strip().lower()
        if item.title and key not in seen:
            result.append(item)
            seen.add(key)
    return result


def _safe_fetch_announcements(
    fetcher: AnnouncementFetcher,
    code: str,
    limit: int,
) -> list[RawSentimentItem]:
    try:
        return fetcher(code, limit)
    except Exception:
        return []


def _safe_fetch_news(fetcher: NewsFetcher, term: str, limit: int) -> list[RawSentimentItem]:
    try:
        return fetcher(term, limit)
    except Exception:
        return []


def _unique_non_empty(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = value.strip()
        if normalized and normalized not in seen:
            result.append(normalized)
            seen.add(normalized)
    return result


def _date_part(value: object) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text[:10] if text else None


def _clean_html(value: str) -> str:
    text = re.sub(r"<[^>]+>", "", value)
    return unescape(re.sub(r"\s+", " ", text)).strip()
