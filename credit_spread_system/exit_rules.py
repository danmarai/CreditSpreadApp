from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional

from credit_spread_system.config import DTE_WARNING_DAYS, NEAR_BREACH_PCT, PROFIT_TARGET_PCT, STOP_LOSS_MULTIPLE
from credit_spread_system.models import Position


class Action(str, Enum):
    CLOSE_BREACH = "CLOSE_BREACH"
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"
    CLOSE_DTE = "CLOSE_DTE"
    EVALUATE = "EVALUATE"
    HOLD = "HOLD"


@dataclass(frozen=True)
class ExitSignal:
    triggered: bool
    reason: str
    threshold: float


def evaluate_profit_target(entry_credit: float, current_spread_value: float) -> ExitSignal:
    target_value = entry_credit * (1 - PROFIT_TARGET_PCT)
    triggered = current_spread_value <= target_value
    return ExitSignal(triggered=triggered, reason="PROFIT_TARGET", threshold=target_value)


def evaluate_stop_loss(entry_credit: float, current_spread_value: float) -> ExitSignal:
    stop_value = entry_credit * STOP_LOSS_MULTIPLE
    triggered = current_spread_value >= stop_value
    return ExitSignal(triggered=triggered, reason="STOP_LOSS", threshold=stop_value)


def evaluate_dte(expiration: date, today: date) -> ExitSignal:
    dte = (expiration - today).days
    triggered = dte <= DTE_WARNING_DAYS
    return ExitSignal(triggered=triggered, reason="DTE_WARNING", threshold=DTE_WARNING_DAYS)


def evaluate_breach(underlying_price: float, short_strike: float) -> ExitSignal:
    triggered = underlying_price <= short_strike
    return ExitSignal(triggered=triggered, reason="STRIKE_BREACH", threshold=short_strike)


def evaluate_near_breach(underlying_price: float, short_strike: float) -> ExitSignal:
    warning_level = short_strike * (1 + NEAR_BREACH_PCT)
    triggered = underlying_price <= warning_level
    return ExitSignal(triggered=triggered, reason="NEAR_BREACH", threshold=warning_level)


def evaluate_position(
    position: Position,
    current_spread_value: Optional[float],
    underlying_price: Optional[float],
    today: Optional[date] = None,
) -> tuple[Action, dict[str, object]]:
    current_day = today or date.today()

    details: dict[str, object] = {
        "position_id": position.position_id,
        "symbol": position.symbol,
        "current_spread_value": current_spread_value,
        "underlying_price": underlying_price,
        "entry_credit": position.entry_credit,
        "expiration": position.expiration,
    }

    if current_spread_value is None or underlying_price is None:
        details["reason"] = "Missing pricing or underlying data"
        return Action.EVALUATE, details

    breach_signal = evaluate_breach(underlying_price, position.short_strike)
    stop_signal = evaluate_stop_loss(position.entry_credit, current_spread_value)
    profit_signal = evaluate_profit_target(position.entry_credit, current_spread_value)
    dte_signal = evaluate_dte(position.expiration, current_day)
    near_breach_signal = evaluate_near_breach(underlying_price, position.short_strike)

    details.update(
        {
            "breach": breach_signal,
            "stop_loss": stop_signal,
            "profit_target": profit_signal,
            "dte_warning": dte_signal,
            "near_breach": near_breach_signal,
        }
    )

    if breach_signal.triggered:
        return Action.CLOSE_BREACH, details
    if stop_signal.triggered:
        return Action.STOP_LOSS, details
    if profit_signal.triggered:
        return Action.TAKE_PROFIT, details
    if dte_signal.triggered:
        return Action.CLOSE_DTE, details
    if near_breach_signal.triggered:
        return Action.EVALUATE, details

    return Action.HOLD, details
