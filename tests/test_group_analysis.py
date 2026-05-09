from backend.app.services.group_analysis import analyze_group
from backend.app.services.metrics import FundPoint, summarize_series


def _summary(code: str, name: str, values: list[float]):
    points = [
        FundPoint(date=f"2026-01-{idx + 1:02d}", net_value=value)
        for idx, value in enumerate(values)
    ]
    return summarize_series(code=code, name=name, points=points)


def test_analyze_group_sorts_members_and_calculates_group_risk():
    members = [
        _summary("501018", "南方原油A", [1.0, 1.1, 0.8, 1.2]),
        _summary("110011", "易方达中小盘", [1.0, 1.02, 1.03, 1.04]),
        _summary("161129", "原油LOF", [1.0, 0.97, 0.96, 0.95]),
    ]

    group = analyze_group(name="oil-watch", members=members)

    assert group.name == "oil-watch"
    assert group.member_count == 3
    assert [member.code for member in group.members] == ["501018", "110011", "161129"]
    assert group.best_member.code == "501018"
    assert group.weakest_member.code == "161129"
    assert group.average_return > 0
    assert group.worst_drawdown == -0.2727
    assert group.risk_level == "high"
    assert "501018" in group.narrative


def test_analyze_group_rejects_empty_groups():
    try:
        analyze_group(name="empty", members=[])
    except ValueError as exc:
        assert "at least one fund" in str(exc)
    else:
        raise AssertionError("empty group should fail")
