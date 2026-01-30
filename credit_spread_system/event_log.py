from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from credit_spread_system.config import EVENT_LOG_RETENTION_DAYS
from credit_spread_system.sheets_client import SheetsClient

logger = logging.getLogger(__name__)

EVENT_TYPES = {
    "IV_RANK_BLOCK",
    "PORTFOLIO_STOP_ALERT",
    "PRICING_FALLBACK",
    "STALE_DATA_WARNING",
    "API_ERROR",
    "PRICING_FAILURE",
}


def log_event(
    event_type: str,
    symbol: str,
    position_id: str | None,
    message: str,
    sheets_client: SheetsClient | None = None,
) -> bool:
    if event_type not in EVENT_TYPES:
        raise ValueError(f"Invalid event type: {event_type}")

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "symbol": symbol,
        "position_id": position_id or "",
        "message": message,
    }

    client = sheets_client or SheetsClient.from_env()
    success = client.append_event_log(event)

    if not success:
        logger.warning("Failed to append event log entry")
    return success


def prune_old_events(
    retention_days: int = EVENT_LOG_RETENTION_DAYS,
    sheets_client: SheetsClient | None = None,
) -> int:
    client = sheets_client or SheetsClient.from_env()
    worksheet = client.get_worksheet("Event_Log")
    if not worksheet:
        return 0

    rows = worksheet.get_all_records()
    if not rows:
        return 0

    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)

    indices_to_delete: list[int] = []
    for idx, row in enumerate(rows, start=2):
        timestamp = _parse_timestamp(row.get("timestamp"))
        if timestamp and timestamp < cutoff:
            indices_to_delete.append(idx)

    deleted = 0
    for row_index in reversed(indices_to_delete):
        worksheet.delete_rows(row_index)
        deleted += 1

    return deleted


def _parse_timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc)
    try:
        parsed = datetime.fromisoformat(str(value))
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None
