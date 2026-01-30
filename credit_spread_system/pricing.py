from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from credit_spread_system.alpaca_client import Quote

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PriceResult:
    price: Optional[float]
    method: str  # MID, LAST, NONE

    @property
    def fallback_used(self) -> bool:
        return self.method == "LAST"


def get_mid_price(bid: Optional[float], ask: Optional[float]) -> Optional[float]:
    if bid is None or ask is None:
        return None
    return (bid + ask) / 2


def get_option_price(quote: Quote | None) -> PriceResult:
    if quote is None:
        return PriceResult(price=None, method="NONE")

    mid = get_mid_price(quote.bid, quote.ask)
    if mid is not None:
        return PriceResult(price=mid, method="MID")

    if quote.last is not None:
        logger.warning("Mid price unavailable; falling back to last price")
        return PriceResult(price=quote.last, method="LAST")

    return PriceResult(price=None, method="NONE")


def get_spread_value(short_leg_price: Optional[float], long_leg_price: Optional[float]) -> Optional[float]:
    if short_leg_price is None or long_leg_price is None:
        return None
    return short_leg_price - long_leg_price


def calculate_pl(entry_credit: float, current_spread_value: float, contracts: int) -> float:
    return (entry_credit - current_spread_value) * 100 * contracts
