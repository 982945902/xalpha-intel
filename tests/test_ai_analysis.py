from backend.app.services.group_analysis import analyze_group
from backend.app.services.metrics import FundPoint, summarize_series


def _summary(code: str, name: str, values: list[float]):
    points = [
        FundPoint(date=f"2026-01-{idx + 1:02d}", net_value=value)
        for idx, value in enumerate(values)
    ]
    return summarize_series(code=code, name=name, points=points)


def test_fund_ai_analysis_uses_codex_runner_when_available():
    from backend.app.services.ai_analysis import analyze_fund_summary

    summary = _summary("501018", "南方原油A", [1.0, 1.1, 0.9, 1.2])

    result = analyze_fund_summary(
        summary,
        runner=lambda prompt: "关注回撤与油价波动，当前适合观察仓位风险。",
    )

    assert result.source == "codex"
    assert result.headline == "Codex 分析"
    assert "油价波动" in result.bullets[0]
    assert "不构成投资建议" in result.disclaimer


def test_fund_ai_analysis_falls_back_to_rules_when_runner_fails():
    from backend.app.services.ai_analysis import analyze_fund_summary

    summary = _summary("501018", "南方原油A", [1.0, 0.8, 1.1])

    def broken_runner(prompt: str) -> str:
        raise RuntimeError("codex unavailable")

    result = analyze_fund_summary(summary, runner=broken_runner)

    assert result.source == "rules"
    assert result.headline == "规则分析"
    assert any("501018" in bullet for bullet in result.bullets)
    assert any("高" in bullet or "high" in bullet for bullet in result.bullets)


def test_group_ai_analysis_mentions_best_and_weakest_members():
    from backend.app.services.ai_analysis import analyze_group_result

    group = analyze_group(
        "oil watch",
        [
            _summary("501018", "南方原油A", [1.0, 1.3]),
            _summary("161129", "原油LOF", [1.0, 0.9]),
        ],
    )

    result = analyze_group_result(group, runner=lambda prompt: "")

    assert result.source == "rules"
    assert any("501018" in bullet for bullet in result.bullets)
    assert any("161129" in bullet for bullet in result.bullets)
