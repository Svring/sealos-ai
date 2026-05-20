from datetime import datetime, timezone


def parse_subscription_expiry(expire_at: str | None) -> datetime | None:
    """Parse Sealos subscription ``ExpireAt`` into UTC.

    Returns ``None`` for missing, unparseable, or sentinel zero dates.
    """
    if not expire_at or not isinstance(expire_at, str):
        return None

    raw = expire_at.strip()
    if not raw or raw.startswith("0001-01-01"):
        return None

    try:
        normalized = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def is_free_subscription_eligible(
    plan_name: str | None,
    expire_at: str | None,
    *,
    now: datetime | None = None,
) -> bool:
    """Free platform quota applies only to active Sealos Free subscriptions."""
    if not plan_name or not isinstance(plan_name, str):
        return False
    if plan_name.strip() != "Free":
        return False

    expires = parse_subscription_expiry(expire_at)
    if expires is None:
        return False

    reference = now or datetime.now(timezone.utc)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=timezone.utc)
    return expires > reference.astimezone(timezone.utc)
