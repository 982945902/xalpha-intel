from __future__ import annotations

from dataclasses import asdict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.app.services.ai_analysis import (
    AIAnalysis,
    analyze_fund_summary,
    analyze_group_result,
)
from backend.app.services.fund_data import get_fund_summary
from backend.app.services.fund_search import search_funds
from backend.app.services.group_analysis import analyze_group
from backend.app.services.sentiment import analyze_fund_sentiment, analyze_group_sentiment


app = FastAPI(title="xalpha-intel", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5178",
        "http://localhost:5178",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class FundAnalyzeRequest(BaseModel):
    code: str = Field(min_length=1, max_length=16)


class GroupAnalyzeRequest(BaseModel):
    name: str = Field(default="fund group", min_length=1, max_length=80)
    codes: list[str] = Field(min_length=1, max_length=20)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "xalpha-intel"}


@app.get("/api/funds/search")
def fund_search(q: str, limit: int = 10):
    try:
        return [asdict(result) for result in search_funds(q, limit=min(max(limit, 1), 20))]
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"fund search failed: {exc}") from exc


@app.get("/api/funds/{code}")
def fund_detail(code: str):
    return _summary_response(code)


@app.get("/api/funds/{code}/summary")
def fund_summary(code: str):
    return _summary_response(code)


@app.post("/api/analyze/fund")
def analyze_fund(request: FundAnalyzeRequest):
    summary = _load_summary(request.code)
    return {
        "summary": asdict(summary),
        "analysis": asdict(analyze_fund_summary(summary)),
    }


@app.post("/api/groups/analyze")
def group_analysis(request: GroupAnalyzeRequest):
    summaries = [_load_summary(code) for code in _unique_codes(request.codes)]
    return asdict(analyze_group(name=request.name, members=summaries))


@app.post("/api/analyze/group")
def analyze_group_with_ai(request: GroupAnalyzeRequest):
    summaries = [_load_summary(code) for code in _unique_codes(request.codes)]
    group = analyze_group(name=request.name, members=summaries)
    return {
        "group": asdict(group),
        "analysis": asdict(analyze_group_result(group)),
    }


@app.post("/api/sentiment/fund")
def fund_sentiment(request: FundAnalyzeRequest):
    summary = _load_summary(request.code)
    return {
        "summary": asdict(summary),
        "sentiment": asdict(analyze_fund_sentiment(summary)),
    }


@app.post("/api/sentiment/group")
def group_sentiment(request: GroupAnalyzeRequest):
    summaries = [_load_summary(code) for code in _unique_codes(request.codes)]
    group = analyze_group(name=request.name, members=summaries)
    return {
        "group": asdict(group),
        "sentiment": asdict(analyze_group_sentiment(request.name, summaries)),
    }


def _summary_response(code: str):
    return asdict(_load_summary(code))


def _load_summary(code: str):
    try:
        return get_fund_summary(code)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"xalpha fetch failed: {exc}") from exc


def _unique_codes(codes: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for code in codes:
        normalized = code.strip()
        if normalized and normalized not in seen:
            unique.append(normalized)
            seen.add(normalized)
    if not unique:
        raise HTTPException(status_code=422, detail="group must include at least one fund code")
    return unique
