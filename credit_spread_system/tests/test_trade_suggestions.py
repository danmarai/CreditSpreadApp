from credit_spread_system.alpaca_client import OptionContract
from credit_spread_system.trade_suggestions import SuggestionEngine


class FakeAlpaca:
    def __init__(self):
        self._history = [
            {"close": 100 + i * 0.5, "volume": 2_000_000, "date": "2026-01-01"}
            for i in range(259)
        ]
        self._history.append({"close": 229.5, "volume": 3_000_000, "date": "2026-01-01"})

    def get_price_history(self, _symbol, days=260):
        return self._history[-days:]

    def get_iv_history(self, _symbol):
        return [20.0, 30.0, 40.0]

    def get_option_chain(self, _symbol, expiration, option_type="put"):
        return [
            OptionContract(
                symbol="SPY",
                expiration=expiration,
                strike=95.0,
                option_type=option_type,
                bid=2.0,
                ask=2.1,
                last=2.05,
                open_interest=600,
            ),
            OptionContract(
                symbol="SPY",
                expiration=expiration,
                strike=90.0,
                option_type=option_type,
                bid=0.3,
                ask=0.35,
                last=0.32,
                open_interest=600,
            ),
        ]


def test_generate_suggestions_returns_candidate():
    engine = SuggestionEngine(FakeAlpaca())
    suggestions = engine.generate_suggestions(["SPY"])

    assert suggestions
    assert suggestions[0].symbol == "SPY"
    assert suggestions[0].credit > 0
