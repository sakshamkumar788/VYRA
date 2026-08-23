
from intelligence.delivery import (
    IntelligenceDeliveryPolicy,
    IntelligenceDeliveryDecision,
)

from intelligence.priority import (
    IntelligencePriorityEngine,
    PriorityDecision,
)

from intelligence.entities import EntityExtractor

from intelligence.deduplication import (
    StoryDeduplicator,
)
from intelligence.ingestion import (
    IntelligenceIngestionEngine,
)
from intelligence.models import IntelligenceStory
from intelligence.scoring import (
    IntelligenceScorer,
    StoryScore,
)
from location.models import ImportantPlace


class IntelligenceEngine:
    """Turns discovered information into personalized priorities."""

    def __init__(
        self,
        ingestion: IntelligenceIngestionEngine,
        scorer: IntelligenceScorer | None = None,
        deduplicator: StoryDeduplicator | None = None,
    ) -> None:
        self.ingestion = ingestion

        self.scorer = (
            scorer
            or IntelligenceScorer()
        )

        self.deduplicator = (
            deduplicator
            or StoryDeduplicator()
        )

        self.entity_extractor = EntityExtractor()

        self.priority_engine = IntelligencePriorityEngine()

        self.delivery_policy = IntelligenceDeliveryPolicy()

    def evaluate(
        self,
        current_location: str | None,
        important_places: list[ImportantPlace],
    ) -> list[
        tuple[
            IntelligenceStory,
            StoryScore,
            PriorityDecision,
            IntelligenceDeliveryDecision,
        ]
    ]:
        """Fetch, merge, and score current intelligence."""

        ingested = (
            self.ingestion.fetch_all()
        )

        source_stories = [
            (
                item.story,
                item.source_name,
            )
            for item in ingested
        ]

        merged = self.deduplicator.merge(
            source_stories
        )

        evaluated: list[
            tuple[IntelligenceStory, StoryScore]
        ] = []

        for item in merged:
            item.story.entities = (
                self.entity_extractor.extract(
                    item.story.title,
                    item.story.summary,
                )
            )

            result = self.scorer.score(
                story=item.story,
                current_location=current_location,
                important_places=important_places,
            )

            decision = self.priority_engine.decide(
                result
            )

            delivery = self.delivery_policy.evaluate(
                decision
            )

            evaluated.append(
                (
                    item.story,
                    result,
                    decision,
                    delivery,
                )
            )

        evaluated.sort(
            key=lambda item: item[1].score,
            reverse=True,
        )

        return evaluated