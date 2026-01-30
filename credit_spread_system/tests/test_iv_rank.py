from credit_spread_system.iv_rank import IvRankService, compute_iv_rank


def test_compute_iv_rank_basic():
    history = [10.0, 12.0, 8.0, 15.0]
    # low=8, high=15, current=15 => 100
    assert compute_iv_rank(history) == 100.0


def test_compute_iv_rank_flat():
    history = [10.0, 10.0, 10.0]
    assert compute_iv_rank(history) == 0.0


def test_iv_rank_cache():
    class FakeAlpaca:
        def __init__(self):
            self.calls = 0

        def get_iv_history(self, _symbol):
            self.calls += 1
            return [10.0, 12.0, 8.0, 15.0]

    service = IvRankService(cache_ttl_seconds=3600)
    alpaca = FakeAlpaca()

    first = service.get_iv_rank("SPY", alpaca, min_iv_rank=30)
    second = service.get_iv_rank("SPY", alpaca, min_iv_rank=30)

    assert first.iv_rank == 100.0
    assert second.iv_rank == 100.0
    assert alpaca.calls == 1


def test_iv_rank_blocked_when_unavailable():
    class FakeAlpaca:
        def get_iv_history(self, _symbol):
            return []

    service = IvRankService(cache_ttl_seconds=3600)
    result = service.get_iv_rank("SPY", FakeAlpaca(), min_iv_rank=30)

    assert result.iv_rank is None
    assert result.blocked is True
