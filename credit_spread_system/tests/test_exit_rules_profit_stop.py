from credit_spread_system.exit_rules import evaluate_profit_target, evaluate_stop_loss


def test_evaluate_profit_target_triggered():
    # Entry credit 1.00 -> target 0.50
    signal = evaluate_profit_target(1.0, 0.5)
    assert signal.triggered is True
    assert signal.threshold == 0.5


def test_evaluate_profit_target_not_triggered():
    signal = evaluate_profit_target(1.0, 0.8)
    assert signal.triggered is False


def test_evaluate_stop_loss_triggered():
    # Entry credit 1.00 -> stop 2.00
    signal = evaluate_stop_loss(1.0, 2.0)
    assert signal.triggered is True
    assert signal.threshold == 2.0


def test_evaluate_stop_loss_not_triggered():
    signal = evaluate_stop_loss(1.0, 1.5)
    assert signal.triggered is False
