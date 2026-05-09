from __future__ import annotations

from dataclasses import dataclass

from backend.app.services.metrics import FundSummary


@dataclass(frozen=True)
class GroupAnalysis:
    name: str
    member_count: int
    members: list[FundSummary]
    best_member: FundSummary
    weakest_member: FundSummary
    average_return: float
    worst_drawdown: float
    risk_level: str
    narrative: str


def analyze_group(name: str, members: list[FundSummary]) -> GroupAnalysis:
    if not members:
        raise ValueError("group must include at least one fund")

    ranked = sorted(members, key=lambda member: member.total_return, reverse=True)
    best = ranked[0]
    weakest = ranked[-1]
    average_return = round(
        sum(member.total_return for member in members) / len(members),
        4,
    )
    worst_drawdown = min(member.max_drawdown for member in members)
    risk_level = _group_risk(members, worst_drawdown)

    return GroupAnalysis(
        name=name,
        member_count=len(members),
        members=ranked,
        best_member=best,
        weakest_member=weakest,
        average_return=average_return,
        worst_drawdown=worst_drawdown,
        risk_level=risk_level,
        narrative=_narrative(name, best, weakest, risk_level, average_return),
    )


def _group_risk(members: list[FundSummary], worst_drawdown: float) -> str:
    if worst_drawdown <= -0.15 or any(member.risk_level == "high" for member in members):
        return "high"
    if worst_drawdown <= -0.08 or any(member.risk_level == "medium" for member in members):
        return "medium"
    return "low"


def _narrative(
    name: str,
    best: FundSummary,
    weakest: FundSummary,
    risk_level: str,
    average_return: float,
) -> str:
    return (
        f"{name} includes {best.code} as the strongest recent performer "
        f"and {weakest.code} as the weakest. Average return is "
        f"{average_return:.2%}; current group risk is {risk_level}."
    )
