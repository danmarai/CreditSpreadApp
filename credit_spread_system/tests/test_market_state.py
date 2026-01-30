from datetime import datetime, timedelta, timezone

from credit_spread_system import market_state


def test_is_market_open_during_session():
    now = datetime(2026, 1, 30, 15, 0, tzinfo=timezone.utc)
    assert market_state.is_market_open(now) is True


def test_is_market_open_after_close():
    now = datetime(2026, 1, 30, 23, 0, tzinfo=timezone.utc)
    assert market_state.is_market_open(now) is False
    assert market_state.is_after_hours(now) is True


def test_is_market_open_weekend():
    now = datetime(2026, 1, 31, 15, 0, tzinfo=timezone.utc)
    assert market_state.is_market_open(now) is False
    assert market_state.is_after_hours(now) is False


def test_is_quote_stale():
    fresh = datetime.now(timezone.utc) - timedelta(seconds=60)
    stale = datetime.now(timezone.utc) - timedelta(seconds=600)

    assert market_state.is_quote_stale(fresh, max_age_seconds=300) is False
    assert market_state.is_quote_stale(stale, max_age_seconds=300) is True


def test_get_market_status_open():
    now = datetime(2026, 1, 30, 15, 0, tzinfo=timezone.utc)
    status = market_state.get_market_status(now)

    assert status["is_open"] is True
    assert status["is_after_hours"] is False
    assert status["message"] == "Market open"
