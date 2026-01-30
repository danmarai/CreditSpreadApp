from credit_spread_system.alpaca_client import AlpacaClient, Quote
from credit_spread_system.data_service import DataService
from credit_spread_system.sheets_client import SheetsClient


class FakeSheets(SheetsClient):
    def __init__(self, rows):
        self._rows = rows
        super().__init__(spreadsheet=None)

    def get_all_positions(self):
        return self._rows


class FakeAlpaca(AlpacaClient):
    def __init__(self):
        super().__init__(options_client=None, market_client=None)

    def get_option_quote(self, symbol, expiration, strike, option_type):
        return Quote(bid=1.0, ask=1.2, last=1.1)

    def get_underlying_price(self, symbol):
        return 100.0


def test_get_enriched_positions():
    rows = [
        {
            "position_id": "1",
            "symbol": "SPY",
            "short_strike": "100",
            "long_strike": "95",
            "expiration": "2026-03-20",
            "entry_credit": "1.0",
            "contracts": "1",
            "status": "OPEN",
        }
    ]

    service = DataService(FakeSheets(rows), FakeAlpaca())
    enriched = service.get_enriched_positions()

    assert len(enriched) == 1
    assert enriched[0].spread_value == 0.0
    assert enriched[0].current_pl == 100.0


def test_get_portfolio_summary():
    rows = [
        {
            "position_id": "1",
            "entry_credit": "1.0",
            "contracts": "1",
            "current_spread_value": "0.5",
            "short_strike": 100.0,
            "long_strike": 95.0,
            "expiration": "2026-03-20",
            "symbol": "SPY",
            "status": "OPEN",
        }
    ]

    service = DataService(FakeSheets(rows), FakeAlpaca())
    summary = service.get_portfolio_summary(portfolio_value=10000)

    assert summary["total_pl"] == 50.0
    assert summary["deployment"] == 0.01


def test_get_market_context():
    service = DataService(FakeSheets([]), FakeAlpaca())
    context = service.get_market_context()

    assert "market_status" in context
