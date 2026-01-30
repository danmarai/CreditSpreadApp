from datetime import date

from credit_spread_system.models import Position
from credit_spread_system.portfolio_risk import (
    calculate_deployment,
    calculate_total_pl,
    check_daily_stop,
    check_weekly_stop,
    rank_positions_by_risk,
)


def make_position(position_id: str, entry_credit: float, short_strike: float, long_strike: float) -> Position:
    return Position(
        position_id=position_id,
        symbol="SPY",
        short_strike=short_strike,
        long_strike=long_strike,
        expiration=date(2026, 3, 20),
        entry_credit=entry_credit,
        contracts=1,
        status="OPEN",
    )


def test_calculate_total_pl():
    positions = [
        make_position("1", 1.0, 100.0, 95.0),
        make_position("2", 0.5, 200.0, 195.0),
    ]
    current_values = {"1": 0.5, "2": 1.0}

    total = calculate_total_pl(positions, current_values)

    assert total == (1.0 - 0.5) * 100 + (0.5 - 1.0) * 100


def test_calculate_deployment():
    positions = [
        make_position("1", 1.0, 100.0, 95.0),
        make_position("2", 0.5, 200.0, 195.0),
    ]

    deployment = calculate_deployment(positions, portfolio_value=10000.0)

    assert deployment == (1.0 * 100 + 0.5 * 100) / 10000.0


def test_stop_breaches():
    daily = check_daily_stop(total_pl=-600, daily_limit=500)
    weekly = check_weekly_stop(total_pl=-1200, weekly_limit=1000)

    assert daily.breached is True
    assert weekly.breached is True


def test_rank_positions_by_risk():
    positions = [
        make_position("1", 1.0, 100.0, 95.0),
        make_position("2", 1.0, 200.0, 195.0),
    ]
    current_values = {"1": 2.0, "2": 1.0}
    underlying_prices = {"1": 99.0, "2": 210.0}

    ranked = rank_positions_by_risk(positions, current_values, underlying_prices)

    assert ranked[0].position_id == "1"
