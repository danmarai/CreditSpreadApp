from datetime import date

from credit_spread_system.exit_rules import evaluate_breach, evaluate_dte, evaluate_near_breach


def test_evaluate_dte_triggered():
    today = date(2026, 1, 30)
    expiration = date(2026, 2, 10)

    signal = evaluate_dte(expiration, today)

    assert signal.triggered is True
    assert signal.threshold == 14


def test_evaluate_dte_not_triggered():
    today = date(2026, 1, 30)
    expiration = date(2026, 3, 20)

    signal = evaluate_dte(expiration, today)

    assert signal.triggered is False


def test_evaluate_breach():
    signal = evaluate_breach(underlying_price=99.0, short_strike=100.0)
    assert signal.triggered is True

    signal = evaluate_breach(underlying_price=101.0, short_strike=100.0)
    assert signal.triggered is False


def test_evaluate_near_breach():
    signal = evaluate_near_breach(underlying_price=100.5, short_strike=100.0)
    assert signal.triggered is True

    signal = evaluate_near_breach(underlying_price=103.0, short_strike=100.0)
    assert signal.triggered is False
