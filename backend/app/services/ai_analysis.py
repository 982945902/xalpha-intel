from __future__ import annotations

from dataclasses import dataclass
import os
import subprocess
from typing import Callable

from backend.app.services.group_analysis import GroupAnalysis
from backend.app.services.metrics import FundSummary

Runner = Callable[[str], str]

DISCLAIMER = "本分析仅用于研究和风险梳理，不构成投资建议。"


@dataclass(frozen=True)
class AIAnalysis:
    source: str
    headline: str
    bullets: list[str]
    disclaimer: str = DISCLAIMER


def analyze_fund_summary(summary: FundSummary, runner: Runner | None = None) -> AIAnalysis:
    prompt = _fund_prompt(summary)
    codex_text = _try_runner(prompt, runner)
    if codex_text:
        return AIAnalysis(source="codex", headline="Codex 分析", bullets=_bullets(codex_text))

    return AIAnalysis(source="rules", headline="规则分析", bullets=_fund_rule_bullets(summary))


def analyze_group_result(group: GroupAnalysis, runner: Runner | None = None) -> AIAnalysis:
    prompt = _group_prompt(group)
    codex_text = _try_runner(prompt, runner)
    if codex_text:
        return AIAnalysis(source="codex", headline="Codex 分析", bullets=_bullets(codex_text))

    return AIAnalysis(source="rules", headline="规则分析", bullets=_group_rule_bullets(group))


def run_codex(prompt: str) -> str:
    command = [
        os.getenv("CODEX_BIN", "codex"),
        "exec",
        "--ephemeral",
        "--sandbox",
        "read-only",
        "-",
    ]
    completed = subprocess.run(
        command,
        input=prompt,
        text=True,
        capture_output=True,
        timeout=float(os.getenv("CODEX_ANALYSIS_TIMEOUT", "45")),
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "codex analysis failed")
    return completed.stdout.strip()


def _try_runner(prompt: str, runner: Runner | None) -> str | None:
    active_runner = runner if runner is not None else run_codex
    try:
        text = active_runner(prompt).strip()
    except Exception:
        return None
    return text or None


def _fund_prompt(summary: FundSummary) -> str:
    return (
        "你是基金研究助手。基于以下结构化指标输出 3-5 条中文要点，"
        "聚焦风险、波动、观察点，不要给直接买卖指令。"
        f"\n基金: {summary.code} {summary.name}"
        f"\n最新净值: {summary.latest_net_value} ({summary.latest_date})"
        f"\n区间收益: {summary.total_return:.2%}"
        f"\n最大回撤: {summary.max_drawdown:.2%}"
        f"\n年化波动: {summary.annualized_volatility:.2%}"
        f"\n风险级别: {summary.risk_level}"
    )


def _group_prompt(group: GroupAnalysis) -> str:
    members = "\n".join(
        f"- {member.code} {member.name}: return={member.total_return:.2%}, "
        f"drawdown={member.max_drawdown:.2%}, vol={member.annualized_volatility:.2%}, "
        f"risk={member.risk_level}"
        for member in group.members
    )
    return (
        "你是基金组合研究助手。基于以下基金组指标输出 3-5 条中文要点，"
        "比较组内强弱、集中风险、观察点，不要给直接买卖指令。"
        f"\n组名: {group.name}"
        f"\n平均收益: {group.average_return:.2%}"
        f"\n最差回撤: {group.worst_drawdown:.2%}"
        f"\n组风险: {group.risk_level}"
        f"\n成员:\n{members}"
    )


def _bullets(text: str) -> list[str]:
    lines = [
        line.strip(" -•\t")
        for line in text.splitlines()
        if line.strip(" -•\t")
    ]
    if not lines:
        return []
    return lines[:5]


def _fund_rule_bullets(summary: FundSummary) -> list[str]:
    return [
        f"{summary.code} {summary.name} 当前风险级别为 {summary.risk_level}。",
        f"观察窗口收益 {summary.total_return:.2%}，最大回撤 {summary.max_drawdown:.2%}。",
        f"年化波动约 {summary.annualized_volatility:.2%}，适合结合持仓比例看承受度。",
    ]


def _group_rule_bullets(group: GroupAnalysis) -> list[str]:
    return [
        f"{group.name} 共 {group.member_count} 只基金，组风险为 {group.risk_level}。",
        f"组内相对最强为 {group.best_member.code}，区间收益 {group.best_member.total_return:.2%}。",
        f"组内相对最弱为 {group.weakest_member.code}，区间收益 {group.weakest_member.total_return:.2%}。",
        f"组合平均收益 {group.average_return:.2%}，最差回撤 {group.worst_drawdown:.2%}。",
    ]
