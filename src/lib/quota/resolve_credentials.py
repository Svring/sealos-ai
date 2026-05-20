import logging
import os
from dataclasses import dataclass
from typing import Literal

from src.lib.quota.free_tier import (
    FreeTierExhaustedError,
    FreeTierSnapshot,
    QuotaUnavailableError,
    free_chat_turns_limit,
    get_free_tier_snapshot,
    refund_free_turn,
    reserve_free_turn,
)
from src.lib.quota.quota_logging import log_billing_decision, log_quota_event
from src.lib.quota.subscription_eligibility import is_free_subscription_eligible

BillingMode = Literal["free", "user"]
DenyReason = Literal[
    "exhausted",
    "no_platform_creds",
    "no_credentials",
    "subscription_ineligible",
]


@dataclass(frozen=True)
class BillingCredentials:
    billing: BillingMode
    base_url: str
    api_key: str
    model_name: str | None
    snapshot: FreeTierSnapshot
    entitlement_key: str


def _trimmed_env(name: str) -> str | None:
    value = os.getenv(name, "").strip()
    return value or None


def resolve_platform_openai_credentials() -> tuple[str, str] | None:
    """Resolve platform-funded OpenAI-compatible credentials, if configured."""
    system_base = _trimmed_env("SYSTEM_OPENAI_API_BASE_URL")
    system_key = _trimmed_env("SYSTEM_OPENAI_API_KEY")
    if system_base and system_key:
        return system_base, system_key

    trial_base = _trimmed_env("TRIAL_BASE_URL")
    trial_key = _trimmed_env("TRIAL_API_KEY")
    if trial_base and trial_key:
        return trial_base, trial_key

    return None


def _empty_snapshot() -> FreeTierSnapshot:
    limit = free_chat_turns_limit()
    return FreeTierSnapshot(limit=limit, used=limit, remaining=0)


def acquire_billing_credentials(
    *,
    entitlement_key: str,
    user_base_url: str | None,
    user_api_key: str | None,
    model_name: str | None,
    plan_name: str | None = None,
    expire_at: str | None = None,
    request_id: str | None = None,
) -> tuple[BillingCredentials | None, DenyReason | Literal["ok"]]:
    """Acquire billing credentials for a single LangGraph streaming run.

    Behaviour:

    1. If platform creds are configured **and** ``plan_name`` is ``Free`` with a
       valid ``expire_at``, atomically ``reserve_free_turn``. On success, return
       ``"free"`` credentials. On exhaustion, fall through to user creds.
    2. If user-provided credentials are present, return ``"user"`` credentials.
    3. Otherwise return ``(None, reason)``:
       - ``"subscription_ineligible"`` → not on Free / subscription expired
       - ``"exhausted"`` → eligible Free tier but quota used up, no user creds
       - ``"no_platform_creds"`` → platform unconfigured AND no user creds

    Raises:
        QuotaUnavailableError: propagated from the quota subsystem. The
            caller MUST translate this to a 503 (fail-closed).
    """
    platform = resolve_platform_openai_credentials()
    platform_configured = platform is not None
    snapshot: FreeTierSnapshot | None = None
    free_eligible = is_free_subscription_eligible(plan_name, expire_at)
    user_credentials_present = bool(
        user_base_url and user_base_url.strip() and user_api_key and user_api_key.strip()
    )

    log_quota_event(
        "acquire_billing_start",
        request_id=request_id,
        entitlement_key=entitlement_key,
        platform_configured=platform_configured,
        free_subscription_eligible=free_eligible,
        user_credentials_present=user_credentials_present,
        plan_name=plan_name,
        expire_at=expire_at,
        model_name=model_name,
    )

    if platform is not None and free_eligible:
        try:
            snapshot = reserve_free_turn(entitlement_key)
        except FreeTierExhaustedError as exc:
            snapshot = None
            log_quota_event(
                "free_turn_reserve_exhausted",
                request_id=request_id,
                entitlement_key=entitlement_key,
                detail=str(exc),
            )
        else:
            base_url, api_key = platform
            log_billing_decision(
                request_id=request_id or "",
                entitlement_key=entitlement_key,
                outcome="granted",
                billing="free",
                snapshot=snapshot,
                plan_name=plan_name,
                expire_at=expire_at,
                user_credentials_present=user_credentials_present,
                platform_configured=platform_configured,
                free_subscription_eligible=free_eligible,
            )
            return (
                BillingCredentials(
                    billing="free",
                    base_url=base_url,
                    api_key=api_key,
                    model_name=model_name,
                    snapshot=snapshot,
                    entitlement_key=entitlement_key,
                ),
                "ok",
            )

    if user_base_url and user_api_key:
        if snapshot is None:
            try:
                snapshot = get_free_tier_snapshot(entitlement_key)
            except QuotaUnavailableError as exc:
                snapshot = _empty_snapshot()
                log_quota_event(
                    "quota_snapshot_unavailable",
                    request_id=request_id,
                    entitlement_key=entitlement_key,
                    detail=str(exc),
                    level=logging.WARNING,
                )
        log_billing_decision(
            request_id=request_id or "",
            entitlement_key=entitlement_key,
            outcome="granted",
            billing="user",
            snapshot=snapshot,
            plan_name=plan_name,
            expire_at=expire_at,
            user_credentials_present=user_credentials_present,
            platform_configured=platform_configured,
            free_subscription_eligible=free_eligible,
            detail="using_user_credentials"
            if user_credentials_present
            else None,
        )
        return (
            BillingCredentials(
                billing="user",
                base_url=user_base_url,
                api_key=user_api_key,
                model_name=model_name,
                snapshot=snapshot,
                entitlement_key=entitlement_key,
            ),
            "ok",
        )

    if platform is None:
        log_billing_decision(
            request_id=request_id or "",
            entitlement_key=entitlement_key,
            outcome="denied",
            deny_reason="no_platform_creds",
            plan_name=plan_name,
            expire_at=expire_at,
            user_credentials_present=user_credentials_present,
            platform_configured=platform_configured,
            free_subscription_eligible=free_eligible,
        )
        return None, "no_platform_creds"
    if not free_eligible:
        log_billing_decision(
            request_id=request_id or "",
            entitlement_key=entitlement_key,
            outcome="denied",
            deny_reason="subscription_ineligible",
            plan_name=plan_name,
            expire_at=expire_at,
            user_credentials_present=user_credentials_present,
            platform_configured=platform_configured,
            free_subscription_eligible=free_eligible,
        )
        return None, "subscription_ineligible"
    log_billing_decision(
        request_id=request_id or "",
        entitlement_key=entitlement_key,
        outcome="denied",
        deny_reason="exhausted",
        plan_name=plan_name,
        expire_at=expire_at,
        user_credentials_present=user_credentials_present,
        platform_configured=platform_configured,
        free_subscription_eligible=free_eligible,
    )
    return None, "exhausted"


__all__ = [
    "BillingCredentials",
    "BillingMode",
    "DenyReason",
    "acquire_billing_credentials",
    "refund_free_turn",
    "resolve_platform_openai_credentials",
]
