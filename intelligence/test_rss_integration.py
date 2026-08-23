from intelligence.ingestion import (
    IntelligenceIngestionEngine,
)
from intelligence.real_sources import (
    RSSIntelligenceSource,
)
from intelligence.models import (
    SourceTrust,
    StoryCategory,
)


def main() -> None:
    source = RSSIntelligenceSource(
        feed_url="https://feeds.bbci.co.uk/news/rss.xml",
        source_name="BBC News",
        category=StoryCategory.WORLD,
        source_trust=SourceTrust.REPUTABLE,
    )

    ingestion = IntelligenceIngestionEngine(
        sources=[source]
    )

    stories = ingestion.fetch_all()

    print("Stories received:", len(stories))

    for item in stories[:3]:
        print()
        print("Title:", item.story.title)
        print("Source:", item.story.source_name if hasattr(item.story, "source_name") else item.story.source)
        print("Category:", item.story.category)
        print("URL:", item.story.url)


if __name__ == "__main__":
    main()