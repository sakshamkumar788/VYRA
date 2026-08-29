from __future__ import annotations

from datetime import datetime
from collections import namedtuple
from typing import Dict

from memory.database import (
    get_category_trends,
    get_delivery_counts_by_type,
    get_total_deliveries,
)

# Minimum number of deliveries before a trend is considered meaningful.
# Below this threshold the output is suppressed to avoid noisy trivial trends.
MIN_DELIVERIES_FOR_TREND = 2

TrendContext = namedtuple(
    "TrendContext",
    [
        "category_trends",   # dict[str, "increasing"|"decreasing"|"stable"]
        "delivery_counts_by_type",  # dict[str, int]
        "total_deliveries_since",  # int
    ],
)


def build_trend_context(
    current_start: datetime,
    current_end: datetime,
    previous_start: datetime,
    previous_end: datetime,
) -> TrendContext:
    """Deterministic builder that calls the 7.90 aggregation APIs.

    No datetime.now() inside this helper.
    """
    category_trends = get_category_trends(current_start, current_end, previous_start, previous_end)
    delivery_counts_by_type = get_delivery_counts_by_type(current_start, current_end)
    total_deliveries_since = get_total_deliveries(current_start, current_end)
    return TrendContext(category_trends, delivery_counts_by_type, total_deliveries_since)


def format_trend_context(trend_ctx: TrendContext) -> str | None:
    """Return a deterministic, description‑only string for the morning briefing.

    The returned sentence never implies user preference; it only describes
    what the delivery history shows.

    Trends are only shown when enough deliveries have been recorded
    (at least :const:`MIN_DELIVERIES_FOR_TREND`); otherwise ``None`` is
    returned so that the morning briefing avoids noisy trivial output.
    """
    if trend_ctx.total_deliveries_since < MIN_DELIVERIES_FOR_TREND:
        return None

    parts: list[str] = []

    # Category trend – pick the first non‑stable trend
    for cat, trend in trend_ctx.category_trends.items():
        if trend != "stable":
            parts.append(f"{cat.upper()} stories are {trend} compared with the previous period.")
            break

    # Delivery‑type counts / total deliveries
    if trend_ctx.total_deliveries_since > 0:
        total = sum(trend_ctx.delivery_counts_by_type.values())
        if total > 0:
            parts.append(f"You received {total} delivery items this period.")

    if not parts:
        return None
    return " ".join(parts)