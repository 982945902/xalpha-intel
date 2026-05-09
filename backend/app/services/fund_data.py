from __future__ import annotations

from backend.app.services.metrics import FundPoint, FundSummary, summarize_series


def get_fund_summary(code: str, limit: int = 260) -> FundSummary:
    import xalpha as xa

    fund = xa.fundinfo(code)
    points = _points_from_price_frame(fund.price, limit=limit)
    return summarize_series(code=code, name=getattr(fund, "name", code), points=points)


def _points_from_price_frame(price_frame, limit: int) -> list[FundPoint]:
    rows = price_frame.sort_values("date").tail(limit)
    points: list[FundPoint] = []
    for row in rows.itertuples(index=False):
        points.append(
            FundPoint(
                date=str(getattr(row, "date"))[:10],
                net_value=float(getattr(row, "netvalue")),
            )
        )

    if not points:
        raise ValueError("xalpha returned no price points for this fund")

    return points
