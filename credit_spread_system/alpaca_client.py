from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Optional

from credit_spread_system.config import load_config

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Quote:
    bid: Optional[float]
    ask: Optional[float]
    last: Optional[float]
    timestamp: Optional[Any] = None


class AlpacaClient:
    def __init__(
        self,
        options_client: Any | None,
        market_client: Any | None,
        cache_ttl_seconds: int = 60,
    ) -> None:
        self._options_client = options_client
        self._market_client = market_client
        self._cache_ttl_seconds = cache_ttl_seconds
        self._quote_cache: dict[str, tuple[float, Any]] = {}

    @classmethod
    def from_env(cls, cache_ttl_seconds: int = 60) -> "AlpacaClient":
        config = load_config()
        options_client = None
        market_client = None

        try:
            from alpaca.data.historical import (  # type: ignore
                OptionHistoricalDataClient,
                StockHistoricalDataClient,
            )

            options_client = OptionHistoricalDataClient(
                api_key=config.alpaca_api_key,
                secret_key=config.alpaca_secret_key,
            )
            market_client = StockHistoricalDataClient(
                api_key=config.alpaca_api_key,
                secret_key=config.alpaca_secret_key,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to initialize Alpaca clients: %s", exc)

        return cls(options_client=options_client, market_client=market_client, cache_ttl_seconds=cache_ttl_seconds)

    def get_option_quote(
        self, symbol: str, expiration: str, strike: float, option_type: str
    ) -> Optional[Quote]:
        cache_key = f"option:{symbol}:{expiration}:{strike}:{option_type}"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        if not self._options_client:
            logger.warning("Option client unavailable; cannot fetch option quote")
            return None

        try:
            raw = self._fetch_option_quote(symbol, expiration, strike, option_type)
            quote = _normalize_quote(raw)
            if quote:
                self._set_cache(cache_key, quote)
            return quote
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to fetch option quote: %s", exc)
            return None

    def get_underlying_price(self, symbol: str) -> Optional[float]:
        cache_key = f"underlying:{symbol}"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        if not self._market_client:
            logger.warning("Market client unavailable; cannot fetch underlying price")
            return None

        try:
            raw = self._fetch_underlying_price(symbol)
            price = _extract_price(raw)
            if price is not None:
                self._set_cache(cache_key, price)
            return price
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to fetch underlying price: %s", exc)
            return None

    def _get_cache(self, key: str) -> Any | None:
        now = time.monotonic()
        cached = self._quote_cache.get(key)
        if not cached:
            return None
        timestamp, value = cached
        if now - timestamp > self._cache_ttl_seconds:
            self._quote_cache.pop(key, None)
            return None
        return value

    def _set_cache(self, key: str, value: Any) -> None:
        self._quote_cache[key] = (time.monotonic(), value)

    def _fetch_option_quote(
        self, symbol: str, expiration: str, strike: float, option_type: str
    ) -> Any:
        client = self._options_client
        if client is None:
            raise RuntimeError("Options client is not configured")
        if hasattr(client, "get_latest_option_quote"):
            return client.get_latest_option_quote(symbol, expiration, strike, option_type)
        if hasattr(client, "get_option_quote"):
            return client.get_option_quote(symbol, expiration, strike, option_type)
        if hasattr(client, "get_quote"):
            return client.get_quote(symbol, expiration, strike, option_type)
        raise AttributeError("Options client does not expose a supported quote method")

    def _fetch_underlying_price(self, symbol: str) -> Any:
        client = self._market_client
        if client is None:
            raise RuntimeError("Market client is not configured")
        if hasattr(client, "get_latest_trade"):
            return client.get_latest_trade(symbol)
        if hasattr(client, "get_latest_quote"):
            return client.get_latest_quote(symbol)
        if hasattr(client, "get_price"):
            return client.get_price(symbol)
        raise AttributeError("Market client does not expose a supported price method")


def _normalize_quote(raw: Any) -> Optional[Quote]:
    if raw is None:
        return None

    if isinstance(raw, dict):
        return Quote(
            bid=_parse_optional_float(raw.get("bid_price", raw.get("bid"))),
            ask=_parse_optional_float(raw.get("ask_price", raw.get("ask"))),
            last=_parse_optional_float(raw.get("last_price", raw.get("last"))),
            timestamp=raw.get("timestamp"),
        )

    bid = _parse_optional_float(getattr(raw, "bid_price", getattr(raw, "bid", None)))
    ask = _parse_optional_float(getattr(raw, "ask_price", getattr(raw, "ask", None)))
    last = _parse_optional_float(getattr(raw, "last_price", getattr(raw, "last", None)))
    timestamp = getattr(raw, "timestamp", None)

    if bid is None and ask is None and last is None:
        return None

    return Quote(bid=bid, ask=ask, last=last, timestamp=timestamp)


def _extract_price(raw: Any) -> Optional[float]:
    if raw is None:
        return None
    if isinstance(raw, dict):
        return _parse_optional_float(
            raw.get("price", raw.get("last_price", raw.get("last")))
        )
    for attr in ("price", "last_price", "last"):
        if hasattr(raw, attr):
            return _parse_optional_float(getattr(raw, attr))
    return None


def _parse_optional_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    return float(value)
