"""Source-native bounded controls for existing Sonnet staleness finding.

This observation program is human authored after reading public reviewer finding.
A fail on historical source is an expected witness, not a test infrastructure error.
"""
from datetime import UTC, datetime

from gimmes.models.market import Market, MarketStatus
from gimmes.strategy.staleness import StalenessEntry, check_staleness


def market(*, recent, cumulative, price=0.65, oi=1000):
    return Market(
        ticker="MG-CHECK",
        status=MarketStatus.ACTIVE,
        yes_bid=price - 0.01,
        yes_ask=price + 0.01,
        last_price=price,
        volume=cumulative,
        volume_24h=recent,
        open_interest=oi,
    )


def initial(*, price=0.65, oi=1000, count=4):
    return {"MG-CHECK": StalenessEntry(
        price=price,
        volume=0,
        open_interest=oi,
        count=count,
        last_cycle=datetime.now(UTC).isoformat(),
    )}


def test_mgcheck_zero_recent_volume_must_not_use_lifetime_history():
    """Native counterexample: no trading in 24h but cumulative historical volume is high."""
    kept, skipped, data = check_staleness(
        [market(recent=0, cumulative=500)],
        initial(), threshold=5, volume_floor=10,
    )
    assert not kept, "inactive, stable market was incorrectly kept due to historical lifetime volume"
    assert skipped == ["MG-CHECK"]
    assert data["MG-CHECK"]["count"] == 5


def test_mgcheck_real_recent_volume_preserved():
    kept, skipped, data = check_staleness(
        [market(recent=500, cumulative=500)],
        initial(), threshold=5, volume_floor=10,
    )
    assert len(kept) == 1 and not skipped and data["MG-CHECK"]["count"] == 0


def test_mgcheck_exact_floor_recent_volume_preserved():
    kept, skipped, data = check_staleness(
        [market(recent=10, cumulative=500)],
        initial(), threshold=5, volume_floor=10,
    )
    assert len(kept) == 1 and not skipped and data["MG-CHECK"]["count"] == 0


def test_mgcheck_recent_zero_and_lifetime_zero_stale():
    kept, skipped, data = check_staleness(
        [market(recent=0, cumulative=0)],
        initial(), threshold=5, volume_floor=10,
    )
    assert not kept and skipped == ["MG-CHECK"] and data["MG-CHECK"]["count"] == 5


def test_mgcheck_price_change_preserves_activity():
    kept, skipped, data = check_staleness(
        [market(recent=0, cumulative=0, price=0.65)],
        initial(price=0.60), threshold=5, volume_floor=10,
    )
    assert len(kept) == 1 and not skipped and data["MG-CHECK"]["count"] == 0


def test_mgcheck_open_interest_change_preserves_activity():
    kept, skipped, data = check_staleness(
        [market(recent=0, cumulative=0, oi=1000)],
        initial(oi=800), threshold=5, volume_floor=10,
    )
    assert len(kept) == 1 and not skipped and data["MG-CHECK"]["count"] == 0


def test_mgcheck_disabled_filter_does_not_change_state():
    old = initial()
    kept, skipped, data = check_staleness(
        [market(recent=0, cumulative=500)], old, threshold=0,
    )
    assert len(kept) == 1 and not skipped and data["MG-CHECK"]["count"] == 4
