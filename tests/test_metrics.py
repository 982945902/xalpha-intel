from backend.app.services.metrics import (
    FundPoint,
    summarize_series,
)


def test_summarize_series_calculates_return_drawdown_and_volatility():
    points = [
        FundPoint(date="2026-01-01", net_value=1.00),
        FundPoint(date="2026-01-02", net_value=1.10),
        FundPoint(date="2026-01-03", net_value=0.88),
        FundPoint(date="2026-01-04", net_value=1.32),
    ]

    summary = summarize_series(code="501018", name="南方原油A", points=points)

    assert summary.code == "501018"
    assert summary.name == "南方原油A"
    assert summary.latest_net_value == 1.32
    assert summary.total_return == 0.32
    assert summary.max_drawdown == -0.2
    assert summary.observation_count == 4
    assert summary.annualized_volatility > 0
    assert summary.risk_level == "high"


def test_summarize_series_handles_single_point_without_fake_risk():
    points = [FundPoint(date="2026-01-01", net_value=1.00)]

    summary = summarize_series(code="000001", name="单点基金", points=points)

    assert summary.latest_net_value == 1.0
    assert summary.total_return == 0
    assert summary.max_drawdown == 0
    assert summary.annualized_volatility == 0
    assert summary.risk_level == "low"
