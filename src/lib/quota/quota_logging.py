import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from src.lib.quota.subscription_eligibility import (
    is_free_subscription_eligible,
    parse_subscription_expiry,
)

logger = logging.getLogger("sealos.free_quota")
_configured = False


def ensure_quota_logging_configured() -> None:
    global _configured
    if _configured:
        return

    level_name = os.getenv("FREE_QUOTA_LOG_LEVEL", "INFO").strip().upper()
    level = getattr(logging, level_name, logging.INFO)

    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(level)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s [free_quota] %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S",
            )
        )
        logger.addHandler(handler)

    logger.propagate = True

    root = logging.getLogger()
    if root.level > level:
        root.setLevel(level)

    _configured = True


def new_request_id() -> str:
    return uuid4().hex[:12]


def mask_secret(value: str | None, visible_tail: int = 4) -> str | None:
    if value is None:
        return None
    trimmed = value.strip()
    if not trimmed:
        return None
    if len(trimmed) <= visible_tail:
        return "***"
    return f"***{trimmed[-visible_tail:]}"


def snapshot_fields(snapshot: Any) -> dict[str, Any] | None:
    if snapshot is None:
        return None
    return {
        "limit": snapshot.limit,
        "used": snapshot.used,
        "remaining": snapshot.remaining,
    }


def describe_subscription(
    plan_name: str | None,
    expire_at: str | None,
) -> dict[str, Any]:
    parsed = parse_subscription_expiry(expire_at)
    eligible = is_free_subscription_eligible(plan_name, expire_at)
    now = datetime.now(timezone.utc)

    reason: str | None = None
    if not plan_name:
        reason = "missing_plan_name"
    elif not isinstance(plan_name, str) or plan_name.strip() != "Free":
        reason = "plan_not_free"
    elif parsed is None:
        reason = "invalid_or_missing_expire_at"
    elif parsed <= now:
        reason = "subscription_expired"
    elif not eligible:
        reason = "not_eligible"

    return {
        "plan_name": plan_name,
        "expire_at": expire_at,
        "parsed_expire_at": parsed.isoformat() if parsed else None,
        "free_subscription_eligible": eligible,
        "ineligible_reason": reason if not eligible else None,
    }


def log_quota_event(event: str, level: int = logging.INFO, **fields: Any) -> None:
    ensure_quota_logging_configured()
    payload = {"event": event, **fields}
    message = json.dumps(payload, default=str)

    logger.log(level, message)
    for handler in logger.handlers:
        handler.flush()
        stream = getattr(handler, "stream", None)
        if stream is not None and hasattr(stream, "flush"):
            stream.flush()

    # Duplicate to root so LangGraph/uvicorn aggregators always see the line.
    logging.getLogger().log(level, message)


def log_request_context(
    *,
    request_id: str,
    path: str,
    entitlement_key: str | None,
    session_id: str | None,
    trial: bool,
    plan_name: str | None,
    expire_at: str | None,
    model_name: str | None,
    user_base_url: str | None,
    user_api_key: str | None,
    platform_configured: bool,
) -> None:
    log_quota_event(
        "request_received",
        request_id=request_id,
        path=path,
        entitlement_key=entitlement_key,
        session_id=session_id,
        trial=trial,
        model_name=model_name,
        client_base_url=user_base_url,
        user_api_key_present=bool(user_api_key and user_api_key.strip()),
        client_api_key=mask_secret(user_api_key),
        platform_configured=platform_configured,
        subscription=describe_subscription(plan_name, expire_at),
    )


def log_billing_decision(
    *,
    request_id: str,
    entitlement_key: str,
    outcome: str,
    billing: str | None = None,
    deny_reason: str | None = None,
    snapshot: Any = None,
    plan_name: str | None = None,
    expire_at: str | None = None,
    user_credentials_present: bool = False,
    platform_configured: bool = False,
    free_subscription_eligible: bool = False,
    detail: str | None = None,
) -> None:
    log_quota_event(
        "billing_decision",
        request_id=request_id,
        entitlement_key=entitlement_key,
        outcome=outcome,
        billing=billing,
        deny_reason=deny_reason,
        quota=snapshot_fields(snapshot),
        user_credentials_present=user_credentials_present,
        platform_configured=platform_configured,
        free_subscription_eligible=free_subscription_eligible,
        subscription=describe_subscription(plan_name, expire_at),
        detail=detail,
    )


def log_request_status(
    *,
    request_id: str,
    phase: str,
    entitlement_key: str,
    **fields: Any,
) -> None:
    """Single-line summary for the full request phase (grep by request_id)."""
    log_quota_event(
        "request_status",
        request_id=request_id,
        phase=phase,
        entitlement_key=entitlement_key,
        **fields,
    )
