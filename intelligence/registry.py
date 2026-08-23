from intelligence.config import (
    SourceCategory,
    SourceConfig,
)
from intelligence.models import SourceTrust


class IntelligenceSourceRegistry:
    """Stores configured VYRA intelligence sources."""

    def __init__(
        self,
        configs: list[SourceConfig] | None = None,
    ) -> None:
        self.configs = configs or []

    def add(
        self,
        config: SourceConfig,
    ) -> None:
        """Register a source."""

        self.configs.append(config)

    def enabled_sources(
        self,
    ) -> list[SourceConfig]:
        """Return enabled sources."""

        return [
            config
            for config in self.configs
            if config.enabled
        ]

    def by_category(
        self,
        category: str,
    ) -> list[SourceConfig]:
        """Return enabled sources in one category."""

        return [
            config
            for config in self.enabled_sources()
            if config.category == category
        ]


def default_source_registry() -> IntelligenceSourceRegistry:
    """Return VYRA's initial verified intelligence sources."""

    registry = IntelligenceSourceRegistry()

    # ---------------------------------------------------------
    # INDIA — official government source
    # ---------------------------------------------------------

    registry.add(
        SourceConfig(
            name="PIB India",
            feed_url=(
                "https://pib.gov.in/"
                "RssMain.aspx?ModId=6&Lang=1&Regid=1"
            ),
            category=SourceCategory.INDIA,
            source_trust=SourceTrust.OFFICIAL,
            max_items=10,
            fetch_interval_minutes=60,
        )
    )

    # ---------------------------------------------------------
    # LOCAL — Jalandhar
    # ---------------------------------------------------------

    registry.add(
        SourceConfig(
            name="Indian Express Jalandhar",
            feed_url=(
                "https://indianexpress.com/"
                "section/cities/jalandhar/feed/"
            ),
            category=SourceCategory.LOCAL,
            source_trust=SourceTrust.REPUTABLE,
            max_items=10,
            fetch_interval_minutes=30,
        )
    )

    # ---------------------------------------------------------
    # INDIA
    # ---------------------------------------------------------

    registry.add(
        SourceConfig(
            name="Indian Express India",
            feed_url=(
                "https://indianexpress.com/"
                "section/india/feed/"
            ),
            category=SourceCategory.INDIA,
            source_trust=SourceTrust.REPUTABLE,
            max_items=10,
            fetch_interval_minutes=60,
        )
    )

    # ---------------------------------------------------------
    # INDIAN TECH
    # ---------------------------------------------------------

    registry.add(
        SourceConfig(
            name="ET Entrepreneur AI",
            feed_url=(
                "https://entrepreneur.economictimes."
                "indiatimes.com/rss/ai"
            ),
            category=SourceCategory.AI,
            source_trust=SourceTrust.REPUTABLE,
            max_items=10,
            fetch_interval_minutes=120,
        )
    )

    # ---------------------------------------------------------
    # INDIAN DEEP TECH
    # ---------------------------------------------------------

    registry.add(
        SourceConfig(
            name="ET Entrepreneur Deeptech",
            feed_url=(
                "https://entrepreneur.economictimes."
                "indiatimes.com/rss/deeptech"
            ),
            category=SourceCategory.RESEARCH,
            source_trust=SourceTrust.REPUTABLE,
            max_items=10,
            fetch_interval_minutes=120,
        )
    )

    return registry