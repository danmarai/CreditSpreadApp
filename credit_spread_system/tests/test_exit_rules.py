from datetime import date
from typing import Optional

from credit_spread_system.exit_rules import Action, evaluate_position
from credit_spread_system.models import Position


def make_position(expiration: Optional[date] = None) -> Position:
    expiry = expiration or date(2026, 3, 20)
    return Position(
        position_id="1",
        symbol="SPY",
        short_strike=100.0,
        long_strike=95.0,
        expiration=expiry,
        entry_credit=1.0,
        contracts=1,
        status="OPEN",
    )


def test_priority_breach_over_stop():
    position = make_position()
    action, _details = evaluate_position(
        position,
        current_spread_value=2.5,  # stop-loss triggered
        underlying_price=99.0,  # breach triggered
        today=date(2026, 1, 30),
    )

    assert action == Action.CLOSE_BREACH


def test_priority_profit_over_dte():
    position = make_position()
    action, _details = evaluate_position(
        position,
        current_spread_value=0.4,  # profit triggered
        underlying_price=105.0,
        today=date(2026, 1, 30),
    )

    assert action == Action.TAKE_PROFIT


def test_near_breach_returns_evaluate():
    position = make_position()
    action, _details = evaluate_position(
        position,
        current_spread_value=1.0,
        underlying_price=100.5,  # within 1% warning band
        today=date(2026, 1, 30),
    )

    assert action == Action.EVALUATE


def test_hold_when_no_conditions():
    position = make_position()
    action, _details = evaluate_position(
        position,
        current_spread_value=1.0,
        underlying_price=110.0,
        today=date(2026, 1, 30),
    )

    assert action == Action.HOLD


def test_missing_data_evaluate():
    position = make_position()
    action, _details = evaluate_position(
        position,
        current_spread_value=None,
        underlying_price=110.0,
        today=date(2026, 1, 30),
    )

    assert action == Action.EVALUATE
