from dataclasses import dataclass


class SourceCategory:
    """Categories used by VYRA intelligence sources."""

    LOCAL = "local"
    INDIA = "india"
    INDIAN_TECH = "indian_tech"
    AI = "ai"
    RESEARCH = "research"
    BUSINESS = "business"
    WORLD = "world"
    COMMUNITY = "community"


@dataclass(frozen=True)
class SourceConfig:
    """Configuration for one intelligence source."""

    name: str
    feed_url: str
    category: str
    source_trust: int

    enabled: bool = True
    max_items: int = 10

    fetch_interval_minutes: int = 60