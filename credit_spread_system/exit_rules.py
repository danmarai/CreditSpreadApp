from __future__ import annotations

from dataclasses import dataclass

from credit_spread_system.config import PROFIT_TARGET_PCT, STOP_LOSS_MULTIPLE


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
