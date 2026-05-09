from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
import os
from uuid import uuid4

from dotenv import load_dotenv
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    delete,
    insert,
    select,
    update,
)
from sqlalchemy.engine import Engine

from backend.app.services.fund_search import search_funds

load_dotenv()

DEFAULT_DATABASE_URL = "sqlite:///./xalpha_intel.db"

metadata = MetaData()

fund_groups = Table(
    "xalpha_fund_groups",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("name", String(80), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)

fund_group_items = Table(
    "xalpha_fund_group_items",
    metadata,
    Column("group_id", String(36), ForeignKey("xalpha_fund_groups.id"), primary_key=True),
    Column("code", String(16), primary_key=True),
    Column("position", Integer, nullable=False),
)


@dataclass(frozen=True)
class SavedFund:
    code: str
    name: str


@dataclass(frozen=True)
class SavedFundGroup:
    id: str
    name: str
    codes: list[str]
    funds: list[SavedFund]
    created_at: str
    updated_at: str


def list_saved_groups() -> list[SavedFundGroup]:
    _ensure_tables()
    with _engine().begin() as connection:
        rows = connection.execute(
            select(fund_groups).order_by(fund_groups.c.updated_at.desc())
        ).mappings()
        groups = [_group_from_row(connection, row) for row in rows]
    return groups


def get_saved_group(group_id: str) -> SavedFundGroup | None:
    _ensure_tables()
    with _engine().begin() as connection:
        row = connection.execute(
            select(fund_groups).where(fund_groups.c.id == group_id)
        ).mappings().first()
        if row is None:
            return None
        return _group_from_row(connection, row)


def create_saved_group(name: str, codes: list[str]) -> SavedFundGroup:
    normalized_codes = _unique_codes(codes)
    group_id = str(uuid4())
    now = _now()
    _ensure_tables()
    with _engine().begin() as connection:
        connection.execute(
            insert(fund_groups).values(
                id=group_id,
                name=_normalize_name(name),
                created_at=now,
                updated_at=now,
            )
        )
        _replace_items(connection, group_id, normalized_codes)
    group = get_saved_group(group_id)
    if group is None:
        raise RuntimeError("created group could not be loaded")
    return group


def update_saved_group(group_id: str, name: str, codes: list[str]) -> SavedFundGroup:
    normalized_codes = _unique_codes(codes)
    _ensure_tables()
    with _engine().begin() as connection:
        result = connection.execute(
            update(fund_groups)
            .where(fund_groups.c.id == group_id)
            .values(name=_normalize_name(name), updated_at=_now())
        )
        if result.rowcount == 0:
            raise ValueError("saved group not found")
        _replace_items(connection, group_id, normalized_codes)
    group = get_saved_group(group_id)
    if group is None:
        raise RuntimeError("updated group could not be loaded")
    return group


def delete_saved_group(group_id: str) -> bool:
    _ensure_tables()
    with _engine().begin() as connection:
        connection.execute(delete(fund_group_items).where(fund_group_items.c.group_id == group_id))
        result = connection.execute(delete(fund_groups).where(fund_groups.c.id == group_id))
    return result.rowcount > 0


def reset_saved_group_store_for_tests() -> None:
    _engine.cache_clear()
    _ensure_tables.cache_clear()
    resolve_fund_name.cache_clear()


@lru_cache(maxsize=512)
def resolve_fund_name(code: str) -> str:
    try:
        matches = search_funds(code, limit=8)
    except Exception:
        return code
    for match in matches:
        if match.code == code:
            return match.name
    return matches[0].name if matches else code


@lru_cache(maxsize=1)
def _engine() -> Engine:
    return create_engine(_sqlalchemy_database_url(), pool_pre_ping=True)


@lru_cache(maxsize=1)
def _ensure_tables() -> None:
    metadata.create_all(_engine())


def _sqlalchemy_database_url() -> str:
    raw_url = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    if raw_url.startswith("postgresql://"):
        return raw_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    if raw_url.startswith("postgres://"):
        return raw_url.replace("postgres://", "postgresql+psycopg2://", 1)
    return raw_url


def _group_from_row(connection, row) -> SavedFundGroup:
    item_rows = connection.execute(
        select(fund_group_items.c.code)
        .where(fund_group_items.c.group_id == row["id"])
        .order_by(fund_group_items.c.position.asc())
    )
    codes = [item.code for item in item_rows]
    return SavedFundGroup(
        id=row["id"],
        name=row["name"],
        codes=codes,
        funds=[SavedFund(code=code, name=resolve_fund_name(code)) for code in codes],
        created_at=_iso(row["created_at"]),
        updated_at=_iso(row["updated_at"]),
    )


def _replace_items(connection, group_id: str, codes: list[str]) -> None:
    connection.execute(delete(fund_group_items).where(fund_group_items.c.group_id == group_id))
    if not codes:
        return
    connection.execute(
        insert(fund_group_items),
        [
            {"group_id": group_id, "code": code, "position": index}
            for index, code in enumerate(codes)
        ],
    )


def _unique_codes(codes: list[str]) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for code in codes:
        value = code.strip()
        if value and value not in seen:
            normalized.append(value)
            seen.add(value)
    if not normalized:
        raise ValueError("saved group must include at least one fund code")
    return normalized


def _normalize_name(name: str) -> str:
    normalized = name.strip()
    if not normalized:
        raise ValueError("saved group name is required")
    return normalized[:80]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()
