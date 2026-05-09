from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from statistics import stdev


@dataclass(frozen=True)
class FundPoint:
    date: str
    net_value: float


@dataclass(frozen=True)
class FundSummary:
    code: str
    name: str
    latest_date: str | None
    latest_net_value: float
    total_return: float
    max_drawdown: float
    annualized_volatility: float
    observation_count: int
    risk_level: str
    points: list[FundPoint]


def summarize_series(code: str, name: str, points: list[FundPoint]) -> FundSummary:
    if not points:
        raise ValueError("fund series must include at least one point")

    values = [float(point.net_value) for point in points]
    total_return = _rounded_ratio(values[-1], values[0])
    max_drawdown = _max_drawdown(values)
    volatility = _annualized_volatility(values)

    return FundSummary(
        code=code,
        name=name,
        latest_date=points[-1].date,
        latest_net_value=round(values[-1], 4),
        total_return=total_return,
        max_drawdown=max_drawdown,
        annualized_volatility=volatility,
        observation_count=len(points),
        risk_level=_risk_level(max_drawdown=max_drawdown, volatility=volatility),
        points=points,
    )


def _rounded_ratio(end: float, start: float) -> float:
    if start == 0:
        return 0
    return round(end / start - 1, 4)


def _max_drawdown(values: list[float]) -> float:
    peak = values[0]
    drawdown = 0.0
    for value in values:
        peak = max(peak, value)
        if peak:
            drawdown = min(drawdown, value / peak - 1)
    return round(drawdown, 4)


def _annualized_volatility(values: list[float]) -> float:
    if len(values) < 2:
        return 0

    returns = [
        values[index] / values[index - 1] - 1
        for index in range(1, len(values))
        if values[index - 1] != 0
    ]
    if len(returns) < 2:
        return 0

    return round(stdev(returns) * sqrt(252), 4)


def _risk_level(max_drawdown: float, volatility: float) -> str:
    if max_drawdown <= -0.15 or volatility >= 0.35:
        return "high"
    if max_drawdown <= -0.08 or volatility >= 0.18:
        return "medium"
    return "low"
