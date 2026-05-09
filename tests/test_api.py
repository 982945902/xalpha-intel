from fastapi.testclient import TestClient

from backend.app.services.group_analysis import analyze_group
from backend.app.services.metrics import FundPoint, summarize_series


def _summary(code: str, name: str, values: list[float]):
    points = [
        FundPoint(date=f"2026-01-{idx + 1:02d}", net_value=value)
        for idx, value in enumerate(values)
    ]
    return summarize_series(code=code, name=name, points=points)


def test_health_endpoint():
    from backend.app.main import app

    response = TestClient(app).get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "xalpha-intel"}


def test_fund_summary_endpoint_uses_service(monkeypatch):
    from backend.app import main

    monkeypatch.setattr(
        main,
        "get_fund_summary",
        lambda code: _summary(code, "南方原油A", [1.0, 1.2]),
    )

    response = TestClient(main.app).get("/api/funds/501018/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == "501018"
    assert body["name"] == "南方原油A"
    assert body["total_return"] == 0.2


def test_group_analyze_endpoint_accepts_multiple_codes(monkeypatch):
    from backend.app import main

    fixtures = {
        "501018": _summary("501018", "南方原油A", [1.0, 1.3]),
        "161129": _summary("161129", "原油LOF", [1.0, 0.9]),
    }

    monkeypatch.setattr(main, "get_fund_summary", lambda code: fixtures[code])
    monkeypatch.setattr(main, "analyze_group", analyze_group)

    response = TestClient(main.app).post(
        "/api/groups/analyze",
        json={"name": "oil group", "codes": ["501018", "161129"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "oil group"
    assert body["member_count"] == 2
    assert body["best_member"]["code"] == "501018"
    assert [member["code"] for member in body["members"]] == ["501018", "161129"]
