from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from credit_spread_system.config import DTE_WARNING_DAYS, NEAR_BREACH_PCT, PROFIT_TARGET_PCT, STOP_LOSS_MULTIPLE


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
