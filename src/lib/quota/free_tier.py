import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone

import psycopg
from psycopg import sql

from src.lib.quota.quota_logging import log_quota_event, snapshot_fields
from src.lib.quota.types import (
    ASSISTANT_DB_SCHEMA,
    ASSISTANT_ENTITLEMENTS_TABLE,
    DEFAULT_FREE_CHAT_TURNS,
)

_TABLE_IDENT = sql.Identifier(ASSISTANT_DB_SCHEMA, ASSISTANT_ENTITLEMENTS_TABLE)


class QuotaUnavailableError(Exception):
    """The quota subsystem cannot make a decision (missing config or DB error).

    Callers MUST fail closed when this is raised — do not silently grant free
    turns when the backing store is unreachable.
    """


class FreeTierExhaustedError(Exception):
    """The caller has no remaining free turns to consume."""


@dataclass(frozen=True)
class FreeTierSnapshot:
    limit: int
    used: int
    remaining: int


def assistant_database_url() -> str | None:
    for key in ("ASSISTANT_DATABASE_URL", "DATABASE_URL"):
        value = os.getenv(key, "").strip()
        if value:
            return value
    return None


def free_chat_turns_limit() -> int:
    raw = os.getenv("FREE_CHAT_TURNS", "").strip()
    if not raw:
        return DEFAULT_FREE_CHAT_TURNS
    try:
        parsed = int(raw)
    except ValueError:
        return DEFAULT_FREE_CHAT_TURNS
    if parsed < 0:
        return DEFAULT_FREE_CHAT_TURNS
    return parsed


def is_system_openai_configured() -> bool:
    api_key = os.getenv("SYSTEM_OPENAI_API_KEY", "").strip()
    base_url = os.getenv("SYSTEM_OPENAI_API_BASE_URL", "").strip()
    return bool(api_key and base_url)


def get_free_tier_snapshot(namespace_key: str) -> FreeTierSnapshot:
    """Read current free-tier usage for ``namespace_key``.

    Raises:
        QuotaUnavailableError: when the entitlements DB is not configured or
            cannot be reached. Callers must fail closed.
    """
    limit = free_chat_turns_limit()
    if limit == 0:
        return FreeTierSnapshot(limit=0, used=0, remaining=0)

    database_url = assistant_database_url()
    if not database_url:
        raise QuotaUnavailableError(
            "ASSISTANT_DATABASE_URL is not configured; refusing to serve free turns"
        )

    query = sql.SQL(
        "SELECT free_turns_used FROM {table} WHERE namespace = %s LIMIT 1"
    ).format(table=_TABLE_IDENT)

    try:
        with psycopg.connect(database_url) as conn:
            row = conn.execute(query, (namespace_key,)).fetchone()
    except psycopg.Error as exc:
        raise QuotaUnavailableError(
            f"Entitlements DB read failed: {exc}"
        ) from exc

    used = int(row[0]) if row else 0
    remaining = max(0, limit - used)
    return FreeTierSnapshot(limit=limit, used=used, remaining=remaining)


def reserve_free_turn(namespace_key: str) -> FreeTierSnapshot:
    """Atomically reserve one free turn for ``namespace_key``.

    This is the only path that decrements remaining turns. It runs the INSERT
    + UPDATE in a single transaction and relies on Postgres row-level locking
    to serialize concurrent reservations. The ``RETURNING`` row tells us
    whether the UPDATE actually applied (i.e. whether ``free_turns_used`` was
    still below the limit when the row lock was acquired).

    Raises:
        QuotaUnavailableError: when the entitlements DB is not configured or
            cannot be reached.
        FreeTierExhaustedError: when the namespace has no remaining turns.
    """
    limit = free_chat_turns_limit()
    if limit == 0:
        raise FreeTierExhaustedError("FREE_CHAT_TURNS is 0; free tier disabled")

    database_url = assistant_database_url()
    if not database_url:
        raise QuotaUnavailableError(
            "ASSISTANT_DATABASE_URL is not configured; refusing to serve free turns"
        )

    now = datetime.now(timezone.utc)

    upsert_query = sql.SQL(
        "INSERT INTO {table} (namespace, free_turns_used, updated_at) "
        "VALUES (%s, 0, %s) "
        "ON CONFLICT (namespace) DO NOTHING"
    ).format(table=_TABLE_IDENT)
    reserve_query = sql.SQL(
        "UPDATE {table} "
        "SET free_turns_used = free_turns_used + 1, updated_at = %s "
        "WHERE namespace = %s AND free_turns_used < %s "
        "RETURNING free_turns_used"
    ).format(table=_TABLE_IDENT)

    try:
        with psycopg.connect(database_url) as conn:
            conn.execute(upsert_query, (namespace_key, now))
            row = conn.execute(
                reserve_query, (now, namespace_key, limit)
            ).fetchone()
    except psycopg.Error as exc:
        raise QuotaUnavailableError(
            f"Entitlements DB write failed: {exc}"
        ) from exc

    if row is None:
        log_quota_event(
            "free_turn_reserve_failed",
            entitlement_key=namespace_key,
            limit=limit,
            reason="exhausted",
        )
        raise FreeTierExhaustedError(
            f"namespace {namespace_key!r} has consumed all {limit} free turns"
        )

    used = int(row[0])
    snapshot = FreeTierSnapshot(limit=limit, used=used, remaining=max(0, limit - used))
    log_quota_event(
        "free_turn_reserved",
        entitlement_key=namespace_key,
        quota=snapshot_fields(snapshot),
    )
    return snapshot


def refund_free_turn(namespace_key: str) -> bool:
    """Best-effort decrement of ``free_turns_used`` for ``namespace_key``.

    Used to undo a ``reserve_free_turn`` when the streaming run failed before
    the user got an answer. Never raises — callers cannot do anything useful
    with a refund failure.

    Returns True if a row was actually decremented, False otherwise.
    """
    if free_chat_turns_limit() == 0:
        return False

    database_url = assistant_database_url()
    if not database_url:
        return False

    now = datetime.now(timezone.utc)
    refund_query = sql.SQL(
        "UPDATE {table} "
        "SET free_turns_used = GREATEST(free_turns_used - 1, 0), updated_at = %s "
        "WHERE namespace = %s AND free_turns_used > 0 "
        "RETURNING free_turns_used"
    ).format(table=_TABLE_IDENT)

    try:
        with psycopg.connect(database_url) as conn:
            row = conn.execute(refund_query, (now, namespace_key)).fetchone()
    except psycopg.Error as exc:
        log_quota_event(
            "free_turn_refund_failed",
            entitlement_key=namespace_key,
            detail=str(exc),
            level=logging.WARNING,
        )
        return False

    refunded = row is not None
    log_quota_event(
        "free_turn_refunded" if refunded else "free_turn_refund_noop",
        entitlement_key=namespace_key,
        refunded=refunded,
        quota_after={"used": int(row[0])} if row else None,
    )
    return refunded
