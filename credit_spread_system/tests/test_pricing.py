import pytest

from credit_spread_system.alpaca_client import Quote
from credit_spread_system.pricing import calculate_pl, get_mid_price, get_option_price, get_spread_value


def test_get_mid_price():
    assert get_mid_price(1.0, 1.2) == 1.1
    assert get_mid_price(0.0, 1.0) == 0.5
    assert get_mid_price(None, 1.0) is None


def test_get_option_price_mid():
    quote = Quote(bid=1.0, ask=1.2, last=1.15)
    result = get_option_price(quote)

    assert result.price == 1.1
    assert result.method == "MID"
    assert result.fallback_used is False


def test_get_option_price_fallback_last():
    quote = Quote(bid=None, ask=None, last=1.05)
    result = get_option_price(quote)

    assert result.price == 1.05
    assert result.method == "LAST"
    assert result.fallback_used is True


def test_get_option_price_none():
    result = get_option_price(None)

    assert result.price is None
    assert result.method == "NONE"


def test_get_spread_value():
    assert get_spread_value(1.2, 0.4) == pytest.approx(0.8)
    assert get_spread_value(None, 0.4) is None


def test_calculate_pl():
    assert calculate_pl(1.25, 0.5, 2) == (1.25 - 0.5) * 100 * 2
    assert calculate_pl(1.00, 1.5, 1) == (1.00 - 1.5) * 100 * 1
