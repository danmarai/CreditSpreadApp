from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable, Optional, Sequence

from credit_spread_system.alpaca_client import AlpacaClient, OptionContract
from credit_spread_system.iv_rank import IvRankService
from credit_spread_system.pricing import get_mid_price

DEFAULT_ETF_UNIVERSE = [
    "SPY",
    "QQQ",
    "IWM",
    "DIA",
    "XLF",
    "XLK",
    "XLV",
    "XLE",
    "XLI",
    "XLP",
    "XLU",
    "XLY",
    "XLB",
    "XLC",
    "GLD",
    "SLV",
    "TLT",
    "IEF",
    "HYG",
    "LQD",
]


@dataclass(frozen=True)
class TradeSuggestion:
    symbol: str
    expiration: str
    short_strike: float
    long_strike: float
    credit: float
    support_level: float
    trend_score: int
    risk_label: str
    reasoning: str


@dataclass(frozen=True)
class TrendSignals:
    above_50_and_rising: bool
    above_20_and_50: bool
    higher_lows: bool


class SuggestionEngine:
    def __init__(self, alpaca: AlpacaClient, iv_service: IvRankService | None = None) -> None:
        self.alpaca = alpaca
        self.iv_service = iv_service or IvRankService()

    def generate_suggestions(self, universe: Iterable[str] | None = None) -> list[TradeSuggestion]:
        symbols = list(universe or DEFAULT_ETF_UNIVERSE)
        suggestions: list[TradeSuggestion] = []

        for symbol in symbols:
            history = self.alpaca.get_price_history(symbol, days=260)
            history_list = list(history) if history else []
            if not history_list:
                continue

            if not _liquid_underlying(history_list):
                continue

            iv_result = self.iv_service.get_iv_rank(symbol, self.alpaca)
            if iv_result.iv_rank is None or iv_result.iv_rank < 30:
                continue

            trend = _compute_trend(history_list)
            if not (trend.above_50_and_rising or trend.above_20_and_50 or trend.higher_lows):
                continue

            support = _find_support(history_list)
            if support is None:
                continue

            expirations = _select_expirations(history_list)
            for expiration in expirations:
                chain = self.alpaca.get_option_chain(symbol, expiration, option_type="put")
                if not chain:
                    continue

                suggestion = _select_spread(chain, support)
                if suggestion is None:
                    continue

                short_strike, long_strike, credit = suggestion
                trend_score = int(trend.above_50_and_rising) + int(trend.above_20_and_50) + int(trend.higher_lows)
                risk_label = _risk_label(
                    support=support,
                    short_strike=short_strike,
                    trend_score=trend_score,
                    iv_rank=iv_result.iv_rank,
                    spread_width=short_strike - long_strike,
                    credit=credit,
                )
                reasoning = _build_reasoning(trend, support, iv_result.iv_rank, credit, short_strike)

                suggestions.append(
                    TradeSuggestion(
                        symbol=symbol,
                        expiration=expiration,
                        short_strike=short_strike,
                        long_strike=long_strike,
                        credit=credit,
                        support_level=support,
                        trend_score=trend_score,
                        risk_label=risk_label,
                        reasoning=reasoning,
                    )
                )

        suggestions.sort(key=lambda s: _risk_score(s))
        return suggestions[:5]


def _liquid_underlying(history: Sequence[dict[str, object]]) -> bool:
    if len(history) < 20:
        return False
    volumes = [_to_float(bar.get("volume")) or 0.0 for bar in history[-20:]]
    avg_volume = sum(volumes) / 20
    return avg_volume >= 1_000_000


def _compute_trend(history: Sequence[dict[str, object]]) -> TrendSignals:
    raw_closes = [_to_float(bar.get("close")) for bar in history]
    closes: list[float] = [value for value in raw_closes if value is not None]
    if len(closes) < 50:
        return TrendSignals(False, False, False)

    ma20 = sum(closes[-20:]) / 20
    ma50 = sum(closes[-50:]) / 50
    above_20_and_50 = closes[-1] > ma20 and closes[-1] > ma50

    ma50_prev = sum(closes[-55:-5]) / 50 if len(closes) >= 55 else ma50
    above_50_and_rising = closes[-1] > ma50 and ma50 > ma50_prev

    recent_lows = closes[-4:]
    higher_lows = recent_lows == sorted(recent_lows)

    return TrendSignals(above_50_and_rising, above_20_and_50, higher_lows)


def _find_support(history: Sequence[dict[str, object]]) -> Optional[float]:
    raw_closes = [_to_float(bar.get("close")) for bar in history]
    closes: list[float] = [value for value in raw_closes if value is not None]
    if len(closes) < 50:
        return None

    ma50 = sum(closes[-50:]) / 50
    ma100 = sum(closes[-100:]) / 100 if len(closes) >= 100 else None
    ma200 = sum(closes[-200:]) / 200 if len(closes) >= 200 else None
    recent_low = min(closes[-20:])

    candidates = [ma for ma in [ma50, ma100, ma200] if ma is not None]
    support = min(candidates, key=lambda ma: abs(ma - recent_low), default=None)
    if support is None:
        return None

    volume = _to_float(history[-1].get("volume")) or 0.0
    avg_volume = sum((_to_float(bar.get("volume")) or 0.0) for bar in history[-20:]) / 20
    if volume < avg_volume * 1.2:
        return None

    return support


def _select_expirations(history: Sequence[dict[str, object]]) -> list[str]:
    # Placeholder: assume the most recent bar date is today and target 30-45 DTE
    today = _parse_history_date(history[-1].get("date")) or date.today()
    return [(today.replace(day=1) + _days(35)).isoformat()]


def _select_spread(chain: list[OptionContract], support: float) -> Optional[tuple[float, float, float]]:
    chain = [c for c in chain if c.option_type.lower() == "put"]
    chain.sort(key=lambda c: c.strike)

    for width in (5.0, 10.0):
        for contract in chain:
            if contract.strike >= support:
                continue
            short_strike = contract.strike
            long_strike = short_strike - width
            long_contract = next((c for c in chain if c.strike == long_strike), None)
            if not long_contract:
                continue
            short_mid = get_mid_price(contract.bid, contract.ask) or contract.last
            long_mid = get_mid_price(long_contract.bid, long_contract.ask) or long_contract.last
            if short_mid is None or long_mid is None:
                continue
            credit = short_mid - long_mid
            if credit <= width / 3:
                continue
            if contract.bid is not None and contract.ask is not None:
                if round(contract.ask - contract.bid, 2) > 0.10:
                    continue
            if contract.open_interest is not None and contract.open_interest < 500:
                continue
            return short_strike, long_strike, credit

    return None


def _risk_label(
    support: float,
    short_strike: float,
    trend_score: int,
    iv_rank: float,
    spread_width: float,
    credit: float,
) -> str:
    distance = (support - short_strike) / support if support else 0
    score = 0
    score += 2 if distance > 0.03 else 1
    score += 2 if trend_score == 3 else 1
    score += 1 if iv_rank >= 50 else 0
    score += 1 if spread_width == 10 else 0
    score += 1 if credit > spread_width / 2 else 0

    if score >= 6:
        return "Conservative"
    if score >= 4:
        return "Moderate"
    return "Aggressive"


def _risk_score(suggestion: TradeSuggestion) -> float:
    if suggestion.risk_label == "Conservative":
        return 0.0
    if suggestion.risk_label == "Moderate":
        return 1.0
    return 2.0


def _build_reasoning(
    trend: TrendSignals, support: float, iv_rank: float, credit: float, short_strike: float
) -> str:
    trend_bits = []
    if trend.above_50_and_rising:
        trend_bits.append("50MA rising")
    if trend.above_20_and_50:
        trend_bits.append("price above 20/50MA")
    if trend.higher_lows:
        trend_bits.append("higher lows")
    trend_text = ", ".join(trend_bits) or "trend mixed"
    return (
        f"Support near {support:.2f}; {trend_text}; IV Rank {iv_rank:.1f}; "
        f"credit {credit:.2f} for short strike {short_strike:.2f}"
    )


def _parse_history_date(value: object) -> Optional[date]:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value).date()
        except ValueError:
            return None
    return None


def _days(count: int):
    from datetime import timedelta

    return timedelta(days=count)


def _to_float(value: object) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None
