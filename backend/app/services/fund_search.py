from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Any


@dataclass(frozen=True)
class FundSearchResult:
    code: str
    name: str
    pinyin: str | None
    category: str | None
    company: str | None
    fund_type: str | None
    latest_net_value: float | None
    latest_date: str | None


Provider = Callable[[str], list[dict[str, Any]]]


def search_funds(keyword: str, provider: Provider | None = None, limit: int = 10) -> list[FundSearchResult]:
    normalized = keyword.strip()
    if not normalized:
        return []

    active_provider = provider if provider is not None else _eastmoney_suggestions
    results: list[FundSearchResult] = []
    for item in active_provider(normalized):
        result = parse_suggestion(item)
        if result is None:
            continue
        results.append(result)
        if len(results) >= limit:
            break
    return results


def parse_suggestion(item: dict[str, Any]) -> FundSearchResult | None:
    code = str(item.get("CODE") or item.get("_id") or "").strip()
    name = str(item.get("NAME") or "").strip()
    if not code or not name or not code.isdigit():
        return None

    base = item.get("FundBaseInfo") or {}
    category = item.get("CATEGORYDESC")
    if category and str(category) != "基金":
        return None

    latest_value = base.get("DWJZ")
    return FundSearchResult(
        code=code,
        name=name,
        pinyin=_optional_text(item.get("JP")),
        category=_optional_text(category),
        company=_optional_text(base.get("JJGS")),
        fund_type=_optional_text(base.get("FTYPE")),
        latest_net_value=float(latest_value) if latest_value not in (None, "") else None,
        latest_date=_optional_text(base.get("FSRQ")),
    )


def _eastmoney_suggestions(keyword: str) -> list[dict[str, Any]]:
    from xalpha.misc import get_ttjj_suggestions

    return get_ttjj_suggestions(keyword)


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
