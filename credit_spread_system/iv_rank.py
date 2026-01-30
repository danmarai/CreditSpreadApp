from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Iterable, Optional

from credit_spread_system.config import MIN_IV_RANK
from credit_spread_system.event_log import log_event

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IvRankResult:
    symbol: str
    iv_rank: Optional[float]
    blocked: bool
    reason: str


class IvRankService:
    def __init__(self, cache_ttl_seconds: int = 3600) -> None:
        self._cache_ttl_seconds = cache_ttl_seconds
        self._cache: dict[str, tuple[float, IvRankResult]] = {}

    def get_iv_rank(
        self,
        symbol: str,
        alpaca_client: object,
        min_iv_rank: int = MIN_IV_RANK,
    ) -> IvRankResult:
        cached = self._get_cache(symbol)
        if cached is not None:
            return cached

        iv_history = _fetch_iv_history(alpaca_client, symbol)
        if not iv_history:
            result = IvRankResult(
                symbol=symbol,
                iv_rank=None,
                blocked=True,
                reason="IV history unavailable",
            )
            log_event(
                event_type="IV_RANK_BLOCK",
                symbol=symbol,
                position_id=None,
                message="IV Rank unavailable; blocking new trade recommendations",
            )
            self._set_cache(symbol, result)
            return result

        iv_rank = compute_iv_rank(iv_history)
        blocked = iv_rank < min_iv_rank
        reason = "IV Rank below minimum" if blocked else "IV Rank OK"

        if blocked:
            log_event(
                event_type="IV_RANK_BLOCK",
                symbol=symbol,
                position_id=None,
                message=f"IV Rank {iv_rank:.2f} below minimum {min_iv_rank}",
            )

        result = IvRankResult(symbol=symbol, iv_rank=iv_rank, blocked=blocked, reason=reason)
        self._set_cache(symbol, result)
        return result

    def _get_cache(self, symbol: str) -> Optional[IvRankResult]:
        cached = self._cache.get(symbol)
        if not cached:
            return None
        timestamp, value = cached
        if time.monotonic() - timestamp > self._cache_ttl_seconds:
            self._cache.pop(symbol, None)
            return None
        return value

    def _set_cache(self, symbol: str, result: IvRankResult) -> None:
        self._cache[symbol] = (time.monotonic(), result)


def compute_iv_rank(iv_history: Iterable[float]) -> float:
    values = list(iv_history)
    if not values:
        raise ValueError("IV history is empty")
    low = min(values)
    high = max(values)
    current = values[-1]
    if high == low:
        return 0.0
    return (current - low) / (high - low) * 100


def _fetch_iv_history(alpaca_client: object, symbol: str) -> Optional[list[float]]:
    try:
        if hasattr(alpaca_client, "get_iv_history"):
            return list(alpaca_client.get_iv_history(symbol))
        if hasattr(alpaca_client, "get_iv_history_for_symbol"):
            return list(alpaca_client.get_iv_history_for_symbol(symbol))
        logger.warning("Alpaca client missing IV history method")
        return None
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to fetch IV history: %s", exc)
        return None
