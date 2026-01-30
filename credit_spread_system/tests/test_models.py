from datetime import date

import pytest
from pydantic import ValidationError

from credit_spread_system.models import Position


def test_position_valid_parse_and_round_trip():
    row = {
        "position_id": "1",
        "symbol": "SPY",
        "short_strike": "450",
        "long_strike": "445",
        "expiration": "2026-02-20",
        "entry_credit": "1.25",
        "contracts": "2",
        "status": "OPEN",
        "exit_price": "",
        "exit_date": "",
        "exit_reason": "",
        "iv_rank_at_entry": "55.5",
    }

    position = Position.from_sheet_row(row)

    assert position.position_id == "1"
    assert position.expiration == date(2026, 2, 20)
    assert position.iv_rank_at_entry == 55.5

    round_trip = position.to_sheet_row()
    assert round_trip["expiration"] == "2026-02-20"
    assert round_trip["exit_price"] == ""


def test_position_invalid_status_raises():
    row = {
        "position_id": "1",
        "symbol": "SPY",
        "short_strike": 450,
        "long_strike": 445,
        "expiration": "2026-02-20",
        "entry_credit": 1.25,
        "contracts": 2,
        "status": "INVALID",
    }

    with pytest.raises(ValidationError):
        Position.from_sheet_row(row)


def test_position_negative_strike_raises():
    row = {
        "position_id": "1",
        "symbol": "SPY",
        "short_strike": -450,
        "long_strike": 445,
        "expiration": "2026-02-20",
        "entry_credit": 1.25,
        "contracts": 2,
        "status": "OPEN",
    }

    with pytest.raises(ValidationError):
        Position.from_sheet_row(row)
