from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Optional, Sequence

from credit_spread_system.config import load_config

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Quote:
    bid: Optional[float]
    ask: Optional[float]
    last: Optional[float]
    timestamp: Optional[Any] = None


@dataclass(frozen=True)
class OptionContract:
    symbol: str
    expiration: str
    strike: float
    option_type: str
    bid: Optional[float]
    ask: Optional[float]
    last: Optional[float]
    open_interest: Optional[int]


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

    def get_price_history(self, symbol: str, days: int = 260) -> Optional[Sequence[dict[str, Any]]]:
        cache_key = f"history:{symbol}:{days}"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        if not self._market_client:
            logger.warning("Market client unavailable; cannot fetch price history")
            return None

        try:
            raw = self._fetch_price_history(symbol, days)
            if raw is not None:
                self._set_cache(cache_key, raw)
            return raw
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to fetch price history: %s", exc)
            return None

    def get_option_chain(
        self,
        symbol: str,
        expiration: str,
        option_type: str = "put",
    ) -> Optional[list[OptionContract]]:
        cache_key = f"chain:{symbol}:{expiration}:{option_type}"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        if not self._options_client:
            logger.warning("Option client unavailable; cannot fetch option chain")
            return None

        try:
            raw = self._fetch_option_chain(symbol, expiration, option_type)
            contracts = _normalize_option_chain(raw)
            if contracts is not None:
                self._set_cache(cache_key, contracts)
            return contracts
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to fetch option chain: %s", exc)
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

    def _fetch_price_history(self, symbol: str, days: int) -> Any:
        client = self._market_client
        if client is None:
            raise RuntimeError("Market client is not configured")
        if hasattr(client, "get_price_history"):
            return client.get_price_history(symbol, days)
        if hasattr(client, "get_bars"):
            return client.get_bars(symbol, days)
        raise AttributeError("Market client does not expose a supported history method")

    def _fetch_option_chain(self, symbol: str, expiration: str, option_type: str) -> Any:
        client = self._options_client
        if client is None:
            raise RuntimeError("Options client is not configured")
        if hasattr(client, "get_option_chain"):
            return client.get_option_chain(symbol, expiration, option_type)
        if hasattr(client, "get_options"):
            return client.get_options(symbol, expiration, option_type)
        raise AttributeError("Options client does not expose a supported chain method")


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


def _normalize_option_chain(raw: Any) -> Optional[list[OptionContract]]:
    if raw is None:
        return None
    contracts: list[OptionContract] = []
    if isinstance(raw, list):
        iterable = raw
    elif hasattr(raw, "data"):
        iterable = raw.data  # type: ignore[attr-defined]
    else:
        iterable = []
    for item in iterable:
        if isinstance(item, dict):
            contracts.append(
                OptionContract(
                    symbol=str(item.get("symbol", "")),
                    expiration=str(item.get("expiration", "")),
                    strike=float(item.get("strike", 0.0)),
                    option_type=str(item.get("option_type", "put")),
                    bid=_parse_optional_float(item.get("bid_price", item.get("bid"))),
                    ask=_parse_optional_float(item.get("ask_price", item.get("ask"))),
                    last=_parse_optional_float(item.get("last_price", item.get("last"))),
                    open_interest=_parse_optional_int(item.get("open_interest")),
                )
            )
        else:
            contracts.append(
                OptionContract(
                    symbol=str(getattr(item, "symbol", "")),
                    expiration=str(getattr(item, "expiration", "")),
                    strike=float(getattr(item, "strike", 0.0)),
                    option_type=str(getattr(item, "option_type", "put")),
                    bid=_parse_optional_float(getattr(item, "bid_price", getattr(item, "bid", None))),
                    ask=_parse_optional_float(getattr(item, "ask_price", getattr(item, "ask", None))),
                    last=_parse_optional_float(getattr(item, "last_price", getattr(item, "last", None))),
                    open_interest=_parse_optional_int(getattr(item, "open_interest", None)),
                )
            )
    return contracts


def _parse_optional_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    return float(value)


def _parse_optional_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    return int(value)
