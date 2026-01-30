from types import SimpleNamespace

from credit_spread_system.alpaca_client import AlpacaClient


def test_get_option_quote_cached(monkeypatch):
    calls = {"count": 0}

    class FakeOptionsClient:
        def get_latest_option_quote(self, *_args):
            calls["count"] += 1
            return {"bid_price": 1.0, "ask_price": 1.2, "last_price": 1.1}

    client = AlpacaClient(options_client=FakeOptionsClient(), market_client=None, cache_ttl_seconds=60)

    times = iter([0.0, 10.0, 20.0])
    monkeypatch.setattr("credit_spread_system.alpaca_client.time.monotonic", lambda: next(times))

    first = client.get_option_quote("SPY", "2026-02-20", 450.0, "put")
    second = client.get_option_quote("SPY", "2026-02-20", 450.0, "put")

    assert calls["count"] == 1
    assert first == second
    assert first is not None
    assert first.bid == 1.0


def test_get_option_quote_no_client_returns_none():
    client = AlpacaClient(options_client=None, market_client=None)
    assert client.get_option_quote("SPY", "2026-02-20", 450.0, "put") is None


def test_get_underlying_price_from_latest_trade():
    class FakeMarketClient:
        def get_latest_trade(self, _symbol):
            return {"price": 503.25}

    client = AlpacaClient(options_client=None, market_client=FakeMarketClient())
    price = client.get_underlying_price("SPY")

    assert price == 503.25


def test_get_underlying_price_handles_object():
    class FakeMarketClient:
        def get_latest_trade(self, _symbol):
            return SimpleNamespace(price=412.5)

    client = AlpacaClient(options_client=None, market_client=FakeMarketClient())
    price = client.get_underlying_price("IWM")

    assert price == 412.5


def test_get_underlying_price_error_returns_none():
    class FakeMarketClient:
        def get_latest_trade(self, _symbol):
            raise RuntimeError("down")

    client = AlpacaClient(options_client=None, market_client=FakeMarketClient())
    price = client.get_underlying_price("QQQ")

    assert price is None
