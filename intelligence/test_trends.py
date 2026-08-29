"""
Tests for Step 7.91 Longitudinal Intelligence Trends.

Uses the existing :mod:`memory.database` aggregation APIs.
No new history table, no preference inference, no delivery changes.
"""

from datetime import datetime

from memory.database import (
    get_category_trends,
    get_delivery_counts_by_type,
    get_total_deliveries,
)
from intelligence.trends import (
    build_trend_context,
    format_trend_context,
    TrendContext,
)


def _clean():
    from memory.database import clear_intelligence_delivery_history
    from memory.database import initialize_database
    initialize_database()
    from memory.database import clear_intelligence_delivery_history
    clear_intelligence_delivery_history()


def test_build_trend_context():
    _clean()
    ctx = build_trend_context(
        datetime(2026, 1, 10), datetime(2026, 1, 20),
        datetime(2026, 1, 1), datetime(2026, 1, 9),
    )
    assert isinstance(ctx, TrendContext)
    assert "category_trends" in ctx._fields
    assert "delivery_counts_by_type" in ctx._fields
    assert "total_deliveries_since" in ctx._fields


def test_format_trend_context():
    _clean()
    # Test with an increasing trend and some deliveries.
    ctx = TrendContext(
        category_trends={"ai": "increasing"},
        delivery_counts_by_type={"intelligence": 2},
        total_deliveries_since=2,
    )
    txt = format_trend_context(ctx)
    assert txt is not None
    assert "AI stories are increasing" in txt

    # Test with stable only → no output
    ctx2 = TrendContext(
        category_trends={"research": "stable"},
        delivery_counts_by_type={},
        total_deliveries_since=0,
    )
    txt2 = format_trend_context(ctx2)
    assert txt2 is None

    # Test empty → None
    ctx3 = TrendContext(
        category_trends={},
        delivery_counts_by_type={},
        total_deliveries_since=0,
    )
    txt3 = format_trend_context(ctx3)
    assert txt3 is None


def test_format_trend_context_no_preference_inference():
    """Verify the output never mentions user liking."""
    ctx = TrendContext(
        category_trends={"ai": "increasing"},
        delivery_counts_by_type={"intelligence": 5},
        total_deliveries_since=5,
    )
    txt = format_trend_context(ctx)
    assert "like" not in txt.lower()
    assert "prefer" not in txt.lower()
    assert "VYRA thinks" not in txt


def test_no_trend_when_too_few_deliveries():
    """Below the minimum delivery count, no trend string is produced."""
    _clean()
    ctx = TrendContext(
        category_trends={"ai": "increasing"},
        delivery_counts_by_type={"intelligence": 1},
        total_deliveries_since=1,
    )
    txt = format_trend_context(ctx)
    assert txt is None, f"Expected None for low delivery count, got {txt}"


def test_trend_when_enough_deliveries():
    """At or above the minimum delivery count, trend string is produced."""
    _clean()
    ctx = TrendContext(
        category_trends={"ai": "increasing"},
        delivery_counts_by_type={"intelligence": 1},
        total_deliveries_since=2,
    )
    txt = format_trend_context(ctx)
    assert txt is not None
    assert "AI stories are increasing" in txt


def test_idempotence():
    """Same inputs → same TrendContext."""
    _clean()
    ctx1 = build_trend_context(
        datetime(2026, 1, 10), datetime(2026, 1, 20),
        datetime(2026, 1, 1), datetime(2026, 1, 9),
    )
    ctx2 = build_trend_context(
        datetime(2026, 1, 10), datetime(2026, 1, 20),
        datetime(2026, 1, 1), datetime(2026, 1, 9),
    )
    assert ctx1 == ctx2


def test_no_llm_calls():
    """Verify source code contains no LLM references."""
    import inspect
    src = inspect.getsource(format_trend_context)
    assert "LLM" not in src and "llm" not in src.lower()


def test_no_database_writes():
    """Verify format_trend_context does not call save_intelligence_delivery."""
    import inspect
    src = inspect.getsource(format_trend_context)
    assert "save_intelligence_delivery" not in src


if __name__ == "__main__":
    test_build_trend_context()
    test_format_trend_context()
    test_format_trend_context_no_preference_inference()
    test_idempotence()
    test_no_llm_calls()
    test_no_database_writes()
    print("All trend tests passed.")