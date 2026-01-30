from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from credit_spread_system.exit_rules import evaluate_breach
from credit_spread_system.models import Position


@dataclass(frozen=True)
class StopResult:
    breached: bool
    message: str


def calculate_total_pl(positions: Iterable[Position], current_values: dict[str, float]) -> float:
    total = 0.0
    for position in positions:
        current_value = current_values.get(position.position_id)
        if current_value is None:
            continue
        total += (position.entry_credit - current_value) * 100 * position.contracts
    return total


def calculate_deployment(positions: Iterable[Position], portfolio_value: float) -> float:
    if portfolio_value <= 0:
        return 0.0
    deployed = 0.0
    for position in positions:
        deployed += position.entry_credit * 100 * position.contracts
    return deployed / portfolio_value


def check_daily_stop(total_pl: float, daily_limit: float) -> StopResult:
    if total_pl <= -abs(daily_limit):
        return StopResult(True, f"Daily stop breached: {total_pl:.2f} <= -{abs(daily_limit):.2f}")
    return StopResult(False, "Daily stop OK")


def check_weekly_stop(total_pl: float, weekly_limit: float) -> StopResult:
    if total_pl <= -abs(weekly_limit):
        return StopResult(True, f"Weekly stop breached: {total_pl:.2f} <= -{abs(weekly_limit):.2f}")
    return StopResult(False, "Weekly stop OK")


def rank_positions_by_risk(
    positions: Iterable[Position],
    current_values: dict[str, float],
    underlying_prices: dict[str, float],
) -> list[Position]:
    scored: list[tuple[float, Position]] = []

    for position in positions:
        current_value = current_values.get(position.position_id)
        if current_value is None:
            continue
        max_loss = max((position.short_strike - position.long_strike) - position.entry_credit, 0)
        if max_loss == 0:
            loss_pct = 0.0
        else:
            loss_pct = max((current_value - position.entry_credit) / max_loss, 0)

        underlying = underlying_prices.get(position.position_id)
        breach_signal = False
        if underlying is not None:
            breach_signal = evaluate_breach(underlying, position.short_strike).triggered

        score = loss_pct + (1.0 if breach_signal else 0.0)
        scored.append((score, position))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [position for _score, position in scored]
