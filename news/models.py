from dataclasses import dataclass


@dataclass
class NewsItem:
    """A normalized news item."""

    title: str
    summary: str | None = None
    source: str | None = None
    url: str | None = None