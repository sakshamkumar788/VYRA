from datetime import datetime

from intelligence.models import (
    IntelligenceStory,
    SourceTrust,
    StoryCategory,
    StoryUrgency,
)

from intelligence.sources import IntelligenceSource


class TestIntelligenceSource(IntelligenceSource):
    """Development source used to test the ingestion pipeline."""

    def fetch(
        self,
    ) -> list[IntelligenceStory]:
        """Return controlled test stories."""

        return [
            IntelligenceStory(
                title="Serious situation in Jalandhar",
                summary=(
                    "A serious event has been reported "
                    "in Jalandhar."
                ),
                source="Test Source",
                category=StoryCategory.LOCAL,
                published_at=datetime.now(),
                location_name="Jalandhar",
                severity=80,
                importance=70,
                confidence=90,
                personal_relevance=0,
                novelty=90,
                source_trust=SourceTrust.HIGH,
                urgency=StoryUrgency.IMMEDIATE,
            ),
            IntelligenceStory(
                title="Interesting AI research",
                summary=(
                    "A new AI research development "
                    "has been reported."
                ),
                source="Test Research",
                category=StoryCategory.RESEARCH,
                published_at=datetime.now(),
                severity=10,
                importance=60,
                confidence=85,
                personal_relevance=70,
                novelty=90,
                source_trust=SourceTrust.HIGH,
                urgency=StoryUrgency.NORMAL,
            ),
        ]