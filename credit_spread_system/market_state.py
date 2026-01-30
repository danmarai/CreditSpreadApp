from __future__ import annotations

import logging
from datetime import datetime, time, timezone
from typing import Any

import pandas_market_calendars as mcal

logger = logging.getLogger(__name__)

NY_TZ = "America/New_York"
MARKET_OPEN = time(9, 30)
MARKET_CLOSE = time(16, 0)


def is_market_open(now: datetime | None = None) -> bool:
    current = _normalize_now(now)
    if not _is_trading_day(current):
        return False

    local_time = current.timetz().replace(tzinfo=None)
    return MARKET_OPEN <= local_time <= MARKET_CLOSE


def is_after_hours(now: datetime | None = None) -> bool:
    current = _normalize_now(now)
    if not _is_trading_day(current):
        return False

    local_time = current.timetz().replace(tzinfo=None)
    return local_time > MARKET_CLOSE


def is_quote_stale(quote_timestamp: datetime | None, max_age_seconds: int = 300) -> bool:
    if quote_timestamp is None:
        return True

    now = datetime.now(timezone.utc)
    timestamp = _ensure_utc(quote_timestamp)
    age_seconds = (now - timestamp).total_seconds()
    return age_seconds > max_age_seconds


def get_market_status(now: datetime | None = None) -> dict[str, Any]:
    current = _normalize_now(now)
    trading_day = _is_trading_day(current)
    open_now = trading_day and is_market_open(current)
    after_hours = trading_day and is_after_hours(current)

    if open_now:
        message = "Market open"
    elif after_hours:
        message = "Market closed - after hours"
    elif trading_day:
        message = "Market closed"
    else:
        message = "Market closed - holiday or weekend"

    return {
        "is_open": open_now,
        "is_after_hours": after_hours,
        "message": message,
    }


def _normalize_now(now: datetime | None) -> datetime:
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return current.astimezone(_ny_tz())


def _ensure_utc(timestamp: datetime) -> datetime:
    if timestamp.tzinfo is None:
        return timestamp.replace(tzinfo=timezone.utc)
    return timestamp.astimezone(timezone.utc)


def _is_trading_day(current: datetime) -> bool:
    try:
        calendar = mcal.get_calendar("NYSE")
        schedule = calendar.schedule(
            start_date=current.date(), end_date=current.date(), tz=NY_TZ
        )
        return not schedule.empty
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to check market calendar: %s", exc)
        # Conservative fallback: treat weekdays as trading days
        return current.weekday() < 5


def _ny_tz() -> Any:
    try:
        from zoneinfo import ZoneInfo

        return ZoneInfo(NY_TZ)
    except Exception:  # noqa: BLE001
        return timezone.utc
