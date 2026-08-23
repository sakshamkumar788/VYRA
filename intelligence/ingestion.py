from dataclasses import dataclass

from intelligence.models import IntelligenceStory
from intelligence.sources import IntelligenceSource


@dataclass
class IngestedStory:
    """A story returned by an intelligence source."""

    story: IntelligenceStory
    source_name: str


class IntelligenceIngestionEngine:
    """Collects normalized stories from multiple sources."""

    def __init__(
        self,
        sources: list[IntelligenceSource] | None = None,
    ) -> None:
        self.sources = sources or []

    def add_source(
        self,
        source: IntelligenceSource,
    ) -> None:
        """Register a new intelligence source."""

        self.sources.append(source)

    def fetch_all(self) -> list[IngestedStory]:
        """Fetch stories from every registered source."""

        results: list[IngestedStory] = []

        for source in self.sources:
            try:
                stories = source.fetch()

            except Exception as error:
                print(
                    f"Intelligence source failed: {error}"
                )
                continue

            source_name = (
                source.__class__.__name__
            )

            for story in stories:
                results.append(
                    IngestedStory(
                        story=story,
                        source_name=source_name,
                    )
                )

        return results