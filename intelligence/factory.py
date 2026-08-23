from intelligence.config import SourceConfig
from intelligence.real_sources import (
    RSSIntelligenceSource,
)


def create_source(
    config: SourceConfig,
) -> RSSIntelligenceSource:
    """Create a source adapter from configuration."""

    return RSSIntelligenceSource(
        feed_url=config.feed_url,
        source_name=config.name,
        category=config.category,
        source_trust=config.source_trust,
        max_items=config.max_items,
    )