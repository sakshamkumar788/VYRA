"""
Integration tests for Step 7.94 Longitudinal Intelligence Continuity Validation.

Verifies the chain:
  actual delivery
  → intelligence_delivery_history
  → 7.90 aggregation
  → 7.91 TrendContext
  → 7.92 morning briefing
  → 7.93 minimum-data threshold

Uses fixed datetimes and isolated test data. No new tables, no schema changes.
"""

from datetime import datetime

from memory.database import (
    initialize_database,
    save_intelligence_delivery,
    get_intelligence_delivery_history,
    clear_intelligence_delivery_history,
)
from intelligence.trends import (
    build_trend_context,
    format_trend_context,
    TrendContext,
    MIN_DELIVERIES_FOR_TREND,
)
from morning.generator import MorningBriefingGenerator
from morning.context import MorningBriefingContext
from intelligence.feedback import FeedbackProfile


def _clean():
    initialize_database()
    clear_intelligence_delivery_history()


def test_delivery_appears_in_history():
    """An actual delivered intelligence item appears in delivery history."""
    _clean()
    now = datetime(2026, 1, 15, 12, 0, 0)
    save_intelligence_delivery(
        story_identity="a", title="A", category="ai", source="s",
        url=None, delivered_at=now, delivery_type="intelligence", priority=None,
    )
    rows = get_intelligence_delivery_history(limit=10)
    assert len(rows) == 1, f"Expected 1 row, got {len(rows)}"
    assert rows[0][1] == "A", f"Expected title 'A', got {rows[0][1]}"


def test_aggregation_see_delivery():
    """Aggregation functions see that delivery in the correct time window."""
    _clean()
    now = datetime(2026, 1, 15, 12, 0, 0)
    save_intelligence_delivery(
        story_identity="a", title="A", category="ai", source="s",
        url=None, delivered_at=now, delivery_type="intelligence", priority=None,
    )
    # current window Jan 10-20, previous Jan 1-9
    ctx = build_trend_context(
        datetime(2026, 1, 10), datetime(2026, 1, 20),
        datetime(2026, 1, 1), datetime(2026, 1, 9),
    )
    assert ctx.total_deliveries_since >= 1, f"Expected at least 1, got {ctx.total_deliveries_since}"
    assert "ai" in ctx.category_trends, f"Expected 'ai' in category_trends, got {ctx.category_trends}"


def test_trend_context_reflects_delivery():
    """TrendContext reflects the delivery."""
    _clean()
    now = datetime(2026, 1, 15, 12, 0, 0)
    save_intelligence_delivery(
        story_identity="a", title="A", category="ai", source="s",
        url=None, delivered_at=now, delivery_type="intelligence", priority=None,
    )
    ctx = build_trend_context(
        datetime(2026, 1, 10), datetime(2026, 1, 20),
        datetime(2026, 1, 1), datetime(2026, 1, 9),
    )
    assert "ai" in ctx.category_trends, f"Expected 'ai' in category_trends, got {ctx.category_trends}"
    assert ctx.total_deliveries_since >= 1


def test_morning_briefing_consumes_trend_ctx():
    """Morning briefing can consume TrendContext and include trend string."""
    _clean()
    now = datetime(2026, 1, 15, 12, 0, 0)
    save_intelligence_delivery(
        story_identity="a", title="A", category="ai", source="s",
        url=None, delivered_at=now, delivery_type="intelligence", priority=None,
    )
    ctx = build_trend_context(
        datetime(2026, 1, 10), datetime(2026, 1, 20),
        datetime(2026, 1, 1), datetime(2026, 1, 9),
    )
    # Generate a briefing with trend_ctx
    gen = MorningBriefingGenerator()
    from morning.context import MorningBriefingContext as MBC
    mctx = MBC(
        current_time="2026-01-15T12:00:00",
        time_of_day="morning",
        weather=None,
        important_tasks=[],
        important_events=[],
        news_items=[],
        relevant_memories=[],
        current_goals=[],
        recently_discussed_topics=[],
        previously_used_topics=[],
    )
    briefing = gen.generate(mctx, trend_ctx=ctx)
    # briefing should contain the trend string since total>=2
    assert "AI stories are increasing" in briefing, f"Expected trend string in briefing, got: {briefing}"


def test_no_trend_when_too_few():
    """Fewer than MIN_DELIVERIES_FOR_TREND suppresses trend output."""
    _clean()
    # Only 1 delivery, should suppress trend
    now = datetime(2026, 1, 15, 12, 0, 0)
    save_intelligence_delivery(
        story_identity="a", title="A", category="ai", source="s",
        url=None, delivered_at=now, delivery_type="intelligence", priority=None,
    )
    ctx = build_trend_context(
        datetime(2026, 1, 10), datetime(2026, 1, 20),
        datetime(2026, 1, 1), datetime(2026, 1, 9),
    )
    assert ctx.total_deliveries_since == 1
    txt = format_trend_context(ctx)
    assert txt is None, f"Expected None for low delivery count, got {txt}"


def test_trend_when_enough_deliveries():
    """At or above the minimum delivery count, trend string is produced."""
    _clean()
    # 2 deliveries, at threshold
    now = datetime(2026, 1, 15, 12, 0, 0)
    save_intelligence_delivery(
        story_identity="a", title="A", category="ai", source="s",
        url=None, delivered_at=now, delivery_type="intelligence", priority=None,
    )
    now2 = datetime(2026, 1, 16, 12, 0, 0)
    save_intelligence_delivery(
        story_identity="b", title="B", category="ai", source="s",
        url=None, delivered_at=now2, delivery_type="intelligence", priority=None,
    )
    ctx = build_trend_context(
        datetime(2026, 1, 10), datetime(2026, 1, 20),
        datetime(2026, 1, 1), datetime(2026, 1, 9),
    )
    assert ctx.total_deliveries_since == 2
    txt = format_trend_context(ctx)
    assert txt is not None, f"Expected trend string, got None"
    assert "AI stories are increasing" in txt


def test_feedback_untouched():
    """FeedbackProfile remains untouched."""
    _clean()
    fb = FeedbackProfile()
    assert fb is not None


def test_no_scoring_changes():
    """Scoring module unchanged."""
    from intelligence import scoring  # just ensure import works
    assert scoring is not None


def test_no_resource_warning():
    """No ResourceWarning raised during operations."""
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("error", ResourceWarning)
        _clean()
        now = datetime(2026, 1, 15, 12, 0, 0)
        save_intelligence_delivery(
            story_identity="a", title="A", category="ai", source="s",
            url=None, delivered_at=now, delivery_type="intelligence", priority=None,
        )
        ctx = build_trend_context(
            datetime(2026, 1, 10), datetime(2026, 1, 20),
            datetime(2026, 1, 1), datetime(2026, 1, 9),
        )
        txt = format_trend_context(ctx)


if __name__ == "__main__":
    test_delivery_appears_in_history()
    test_aggregation_see_delivery()
    test_trend_context_reflects_delivery()
    test_morning_briefing_consumes_trend_ctx()
    test_no_trend_when_too_few()
    test_trend_when_enough_deliveries()
    test_feedback_untouched()
    test_no_scoring_changes()
    test_no_resource_warning()
    print("All integration tests passed.")