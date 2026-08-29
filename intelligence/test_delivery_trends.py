"""
Tests for Step 7.90 Longitudinal Intelligence Trends.

Uses the existing intelligence_delivery_history table.
No new history table, no preference inference, no delivery changes.
"""

from datetime import datetime

from memory.database import (
    get_delivery_counts_by_category,
    get_delivery_counts_by_source,
    get_delivery_counts_by_type,
    get_total_deliveries,
    get_category_trends,
    clear_intelligence_delivery_history,
    save_intelligence_delivery,
    get_intelligence_delivery_history,
)


def _clean():
    clear_intelligence_delivery_history()


def test_empty_history():
    _clean()
    counts = get_delivery_counts_by_category(datetime(2026, 1, 1), datetime(2026, 12, 31))
    assert counts == {}, f"Expected empty dict, got {counts}"
    counts_src = get_delivery_counts_by_source(datetime(2026, 1, 1), datetime(2026, 12, 31))
    assert counts_src == {}, f"Expected empty dict, got {counts_src}"
    counts_type = get_delivery_counts_by_type(datetime(2026, 1, 1), datetime(2026, 12, 31))
    assert counts_type == {}, f"Expected empty dict, got {counts_type}"
    total = get_total_deliveries(datetime(2026, 1, 1), datetime(2026, 12, 31))
    assert total == 0, f"Expected 0, got {total}"
    trends = get_category_trends(
        datetime(2026, 1, 1), datetime(2026, 6, 30),
        datetime(2026, 7, 1), datetime(2026, 12, 31),
    )
    assert trends == {}, f"Expected empty dict, got {trends}"


def test_category_counts():
    _clean()
    now = datetime(2026, 1, 15, 12, 0, 0)
    save_intelligence_delivery(
        story_identity="a", title="A", category="ai", source="s",
        url=None, delivered_at=now, delivery_type="intelligence", priority="important",
    )
    now2 = datetime(2026, 1, 20, 12, 0, 0)
    save_intelligence_delivery(
        story_identity="b", title="B", category="ai", source="s",
        url=None, delivered_at=now2, delivery_type="intelligence", priority=None,
    )
    now3 = datetime(2026, 2, 1, 12, 0, 0)
    save_intelligence_delivery(
        story_identity="c", title="C", category="research", source="s",
        url=None, delivered_at=now3, delivery_type="discovery", priority=None,
    )
    counts = get_delivery_counts_by_category(datetime(2026, 1, 1), datetime(2026, 2, 28))
    assert counts.get("ai") == 2, f"Expected ai=2, got {counts}"
    assert counts.get("research") == 1, f"Expected research=1, got {counts}"
    # unknown category should map to "unknown" per implementation
    # but our implementation maps None to "unknown"; here categories are set.


def test_source_counts():
    _clean()
    now = datetime(2026, 1, 10, 12, 0, 0)
    save_intelligence_delivery(
        story_identity="a", title="A", category="ai", source="Indian Express",
        url=None, delivered_at=now, delivery_type="intelligence", priority=None,
    )
    now2 = datetime(2026, 1, 20, 12, 0, 0)
    save_intelligence_delivery(
        story_identity="b", title="B", category="ai", source="ET",
        url=None, delivered_at=now2, delivery_type="intelligence", priority=None,
    )
    counts = get_delivery_counts_by_source(datetime(2026, 1, 1), datetime(2026, 1, 31))
    assert counts.get("Indian Express") == 1
    assert counts.get("ET") == 1


def test_delivery_type_counts():
    _clean()
    now = datetime(2026, 1, 5, 12, 0, 0)
    save_intelligence_delivery(
        story_identity="a", title="A", category="ai", source="s",
        url=None, delivered_at=now, delivery_type="discovery", priority=None,
    )
    now2 = datetime(2026, 1, 10, 12, 0, 0)
    save_intelligence_delivery(
        story_identity="b", title="B", category="ai", source="s",
        url=None, delivered_at=now2, delivery_type="fun_fact", priority=None,
    )
    now3 = datetime(2026, 1, 15, 12, 0, 0)
    save_intelligence_delivery(
        story_identity="c", title="C", category="ai", source="s",
        url=None, delivered_at=now3, delivery_type="humor", priority=None,
    )
    counts = get_delivery_counts_by_type(datetime(2026, 1, 1), datetime(2026, 1, 31))
    assert counts.get("discovery") == 1
    assert counts.get("fun_fact") == 1
    assert counts.get("humor") == 1


def test_total_deliveries():
    _clean()
    now = datetime(2026, 1, 1, 12, 0, 0)
    save_intelligence_delivery(
        story_identity="a", title="A", category="ai", source="s",
        url=None, delivered_at=now, delivery_type="intelligence", priority=None,
    )
    total = get_total_deliveries(datetime(2026, 1, 1), datetime(2026, 1, 31))
    assert total == 1, f"Expected 1, got {total}"


def test_start_boundary_included():
    _clean()
    # Row delivered_at exactly start_time should be included
    now = datetime(2026, 1, 5, 12, 0, 0)
    save_intelligence_delivery(
        story_identity="a", title="A", category="ai", source="s",
        url=None, delivered_at=now, delivery_type="intelligence", priority=None,
    )
    # Row delivered_at one second after start should be included
    now2 = datetime(2026, 1, 5, 12, 0, 1)
    save_intelligence_delivery(
        story_identity="b", title="B", category="ai", source="s",
        url=None, delivered_at=now2, delivery_type="intelligence", priority=None,
    )
    # Row before start excluded
    now3 = datetime(2026, 1, 4, 12, 0, 0)
    save_intelligence_delivery(
        story_identity="c", title="C", category="ai", source="s",
        url=None, delivered_at=now3, delivery_type="intelligence", priority=None,
    )
    counts = get_delivery_counts_by_category(datetime(2026, 1, 5), datetime(2026, 1, 6))
    # only rows with delivered_at >= start and < end (2026-01-06)
    # start=2026-01-05 included, end=2026-01-06 excluded
    # row at 2026-01-04 excluded, row at 2026-01-05 and 2026-01-05:00:01 included
    assert counts.get("ai") == 2, f"Expected 2, got {counts}"


def test_end_boundary_excluded():
    _clean()
    now = datetime(2026, 1, 5, 12, 0, 0)
    save_intelligence_delivery(
        story_identity="a", title="A", category="ai", source="s",
        url=None, delivered_at=now, delivery_type="intelligence", priority=None,
    )
    # Row at exactly end excluded
    now2 = datetime(2026, 1, 5, 12, 0, 1)
    save_intelligence_delivery(
        story_identity="b", title="B", category="ai", source="s",
        url=None, delivered_at=now2, delivery_type="intelligence", priority=None,
    )
    counts = get_delivery_counts_by_category(datetime(2026, 1, 5), datetime(2026, 1, 5, 12, 0, 0))
    # end is exclusive, so only rows with delivered_at >= start and < end (midnight next day?)
    # The row at start timestamp is >= start but < end? end is same timestamp, so < end is false, thus excluded.
    # The row at 12:00:01 is > end, also excluded. So count should be 0.
    assert counts.get("ai", 0) == 0, f"Expected 0 (end exclusive), got {counts}"


def test_recent_history_unchanged():
    _clean()
    # Ensure get_intelligence_delivery_history still works with limit
    now = datetime(2026, 1, 1, 12, 0, 0)
    save_intelligence_delivery(
        story_identity="a", title="A", category="ai", source="s",
        url=None, delivered_at=now, delivery_type="intelligence", priority=None,
    )
    rows = get_intelligence_delivery_history(limit=5)
    assert len(rows) == 1, f"Expected 1, got {len(rows)}"


def test_increasing_trend():
    _clean()
    # Previous window Jan 1-10: 1 item in category tech
    save_intelligence_delivery(
        story_identity="p1", title="P1", category="tech", source="s",
        url=None, delivered_at=datetime(2026, 1, 5), delivery_type="intelligence", priority=None,
    )
    # Current window Jan 15-25: 3 items in category tech
    save_intelligence_delivery(
        story_identity="c1", title="C1", category="tech", source="s",
        url=None, delivered_at=datetime(2026, 1, 15), delivery_type="intelligence", priority=None,
    )
    save_intelligence_delivery(
        story_identity="c2", title="C2", category="tech", source="s",
        url=None, delivered_at=datetime(2026, 1, 18), delivery_type="intelligence", priority=None,
    )
    save_intelligence_delivery(
        story_identity="c3", title="C3", category="tech", source="s",
        url=None, delivered_at=datetime(2026, 1, 22), delivery_type="intelligence", priority=None,
    )
    trends = get_category_trends(
        datetime(2026, 1, 15), datetime(2026, 1, 25),  # current Jan 15-25
        datetime(2026, 1, 1), datetime(2026, 1, 11),      # previous Jan 1-10
    )
    assert trends.get("tech") == "increasing", f"Expected increasing, got {trends}"


def test_decreasing_trend():
    _clean()
    # Previous window Jan 1-10: 3 items in category sports
    save_intelligence_delivery(
        story_identity="p1", title="P1", category="sports", source="s",
        url=None, delivered_at=datetime(2026, 1, 2), delivery_type="intelligence", priority=None,
    )
    save_intelligence_delivery(
        story_identity="p2", title="P2", category="sports", source="s",
        url=None, delivered_at=datetime(2026, 1, 5), delivery_type="intelligence", priority=None,
    )
    save_intelligence_delivery(
        story_identity="p3", title="P3", category="sports", source="s",
        url=None, delivered_at=datetime(2026, 1, 8), delivery_type="intelligence", priority=None,
    )
    # Current window Jan 20-30: 1 item in category sports
    save_intelligence_delivery(
        story_identity="c1", title="C1", category="sports", source="s",
        url=None, delivered_at=datetime(2026, 1, 25), delivery_type="intelligence", priority=None,
    )
    trends = get_category_trends(
        datetime(2026, 1, 20), datetime(2026, 1, 31),  # current Jan 20-31
        datetime(2026, 1, 1), datetime(2026, 1, 11),      # previous Jan 1-10
    )
    assert trends.get("sports") == "decreasing", f"Expected decreasing, got {trends}"


def test_stable_trend():

    _clean()

    # Same count in both non-overlapping windows
    save_intelligence_delivery(
        story_identity="p1",
        title="P1",
        category="music",
        source="s",
        url=None,
        delivered_at=datetime(2026, 1, 2),
        delivery_type="intelligence",
        priority=None,
    )

    save_intelligence_delivery(
        story_identity="p2",
        title="P2",
        category="music",
        source="s",
        url=None,
        delivered_at=datetime(2026, 1, 5),
        delivery_type="intelligence",
        priority=None,
    )

    save_intelligence_delivery(
        story_identity="c1",
        title="C1",
        category="music",
        source="s",
        url=None,
        delivered_at=datetime(2026, 1, 15),
        delivery_type="intelligence",
        priority=None,
    )

    save_intelligence_delivery(
        story_identity="c2",
        title="C2",
        category="music",
        source="s",
        url=None,
        delivered_at=datetime(2026, 1, 18),
        delivery_type="intelligence",
        priority=None,
    )

    trends = get_category_trends(
        datetime(2026, 1, 11),
        datetime(2026, 1, 20),
        datetime(2026, 1, 1),
        datetime(2026, 1, 10),
    )

    assert trends.get("music") == "stable", (
        f"Expected stable, got {trends}"
    )


def test_missing_category_treated_as_zero():
    _clean()
    # Only current window has category "tech", previous has none
    save_intelligence_delivery(
        story_identity="c1", title="C1", category="tech", source="s",
        url=None, delivered_at=datetime(2026, 1, 15), delivery_type="intelligence", priority=None,
    )
    trends = get_category_trends(
        datetime(2026, 1, 1), datetime(2026, 1, 20),
        datetime(2026, 1, 1), datetime(2026, 1, 10),
    )
    assert trends.get("tech") == "increasing", f"Expected increasing, got {trends}"
    # category "sports" missing in both -> stable (0 vs 0)
    assert trends.get("sports") is None, (
        f"Expected missing category to be absent, got {trends}"
    )


def test_no_feedback_profile_interaction():
    """Verify functions do not import or use FeedbackProfile."""
    import inspect
    src = inspect.getsource(get_delivery_counts_by_category)
    assert "FeedbackProfile" not in src, "get_delivery_counts_by_category should not reference FeedbackProfile"
    src = inspect.getsource(get_category_trends)
    assert "FeedbackProfile" not in src, "get_category_trends should not reference FeedbackProfile"


def test_no_llm_calls():
    """Verify no LLM-related imports."""
    import inspect
    for fn in [get_delivery_counts_by_category, get_delivery_counts_by_source,
               get_delivery_counts_by_type, get_total_deliveries, get_category_trends]:
        src = inspect.getsource(fn)
        assert "LLM" not in src and "llm" not in src.lower(), f"{fn.__name__} should not contain LLM references"


def test_no_delivery_history_writes():
    """Verify functions are read-only; they should not call save_intelligence_delivery."""
    import inspect
    for fn in [get_delivery_counts_by_category, get_delivery_counts_by_source,
               get_delivery_counts_by_type, get_total_deliveries, get_category_trends]:
        src = inspect.getsource(fn)
        assert "save_intelligence_delivery" not in src, f"{fn.__name__} should not call save_intelligence_delivery"


if __name__ == "__main__":
    test_empty_history()
    test_category_counts()
    test_source_counts()
    test_delivery_type_counts()
    test_total_deliveries()
    test_start_boundary_included()
    test_end_boundary_excluded()
    test_recent_history_unchanged()
    test_increasing_trend()
    test_decreasing_trend()
    test_stable_trend()
    test_missing_category_treated_as_zero()
    test_no_feedback_profile_interaction()
    test_no_llm_calls()
    test_no_delivery_history_writes()
    print("All delivery trend tests passed.")