from backend.app.services.metrics import FundPoint, summarize_series


def _summary(code: str, name: str, values: list[float]):
    points = [
        FundPoint(date=f"2026-01-{idx + 1:02d}", net_value=value)
        for idx, value in enumerate(values)
    ]
    return summarize_series(code=code, name=name, points=points)


def test_fund_sentiment_combines_announcements_news_and_codex_summary():
    from backend.app.services.sentiment import RawSentimentItem, analyze_fund_sentiment

    summary = _summary("501018", "南方原油A", [1.0, 1.1, 1.05, 1.2])

    def fetch_announcements(code: str, limit: int):
        return [
            RawSentimentItem(
                title="南方原油证券投资基金溢价风险提示公告",
                source="东方财富基金公告",
                published_at="2026-05-07",
                url="https://example.com/report",
                content="基金二级市场交易价格存在溢价风险。",
            )
        ]

    def fetch_news(term: str, limit: int):
        if term != "原油":
            return []
        return [
            RawSentimentItem(
                title="OPEC减产消息提振原油价格",
                source="Google News",
                published_at="2026-05-07",
                url="https://example.com/news",
                content="减产与库存下降对油价形成支撑。",
            )
        ]

    result = analyze_fund_sentiment(
        summary,
        fetch_announcements=fetch_announcements,
        fetch_news=fetch_news,
        runner=lambda prompt: "原油消息偏利好，但基金公告提示溢价风险，整体需要看溢价与油价方向。",
    )

    assert result.subject_type == "fund"
    assert result.subject == "501018 南方原油A"
    assert "原油" in result.keywords
    assert result.bullish_count == 1
    assert result.bearish_count == 1
    assert result.stance == "mixed"
    assert result.analysis_source == "codex"
    assert "溢价风险" in result.summary
    assert [item.tone for item in result.items] == ["bearish", "bullish"]


def test_sentiment_rules_classify_price_support_as_bullish():
    from backend.app.services.sentiment import RawSentimentItem, classify_sentiment_item

    item = classify_sentiment_item(
        RawSentimentItem(
            title="库存下降带动原油价格上涨",
            source="news",
            published_at=None,
            url=None,
            content="需求回暖，美元走弱。",
        )
    )

    assert item.tone == "bullish"
    assert item.confidence >= 0.7
    assert "库存下降" in item.reason


def test_group_sentiment_deduplicates_items_and_reports_group_subject():
    from backend.app.services.sentiment import RawSentimentItem, analyze_group_sentiment

    members = [
        _summary("501018", "南方原油A", [1.0, 1.2]),
        _summary("161129", "原油LOF", [1.0, 0.95]),
    ]

    def fetch_announcements(code: str, limit: int):
        return []

    def fetch_news(term: str, limit: int):
        return [
            RawSentimentItem(
                title="OPEC减产消息提振原油价格",
                source="Google News",
                published_at="2026-05-07",
                url="https://example.com/news",
                content="减产影响原油供给。",
            )
        ]

    result = analyze_group_sentiment(
        "原油观察组",
        members,
        fetch_announcements=fetch_announcements,
        fetch_news=fetch_news,
        runner=lambda prompt: "",
    )

    assert result.subject_type == "group"
    assert result.subject == "原油观察组"
    assert result.bullish_count == 1
    assert len(result.items) == 1
    assert result.analysis_source == "rules"
