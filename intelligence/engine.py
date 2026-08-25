from intelligence.discovery import DiscoveryEngine

from intelligence.geography import (
    GeographicRelevanceEngine,
)

from intelligence.tech_relevance import (
    TechnologyRelevanceEngine,
)

from intelligence.india_relevance import (
    IndiaRelevanceEngine,
)

from intelligence.world_relevance import (
    WorldRelevanceEngine,
)

from intelligence.queue import IntelligenceQueue

from intelligence.selection import IntelligenceSelector

from intelligence.delivery import (
    IntelligenceDeliveryPolicy,
    IntelligenceDeliveryDecision,
)

from intelligence.priority import (
    IntelligencePriority,
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

from intelligence.feedback import FeedbackProfile

from intelligence.feedback_handler import (
    IntelligenceFeedbackHandler,
)

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
        feedback_profile: FeedbackProfile | None = None,
    ) -> None:
        self.ingestion = ingestion

        self.feedback_profile = (
            feedback_profile
            or FeedbackProfile()
        )

        self.feedback_profile.load_persistent_feedback()

        self.feedback_handler = (
            IntelligenceFeedbackHandler(
                self.feedback_profile
            )
        )

        self.scorer = (
            scorer
            or IntelligenceScorer(
                self.feedback_profile
            )
        )

        self.deduplicator = (
            deduplicator
            or StoryDeduplicator()
        )

        self.entity_extractor = EntityExtractor()

        self.priority_engine = IntelligencePriorityEngine()

        self.delivery_policy = IntelligenceDeliveryPolicy()

        self.selector = IntelligenceSelector()

        self.geographic_engine = (
            GeographicRelevanceEngine()
        )

        self.india_relevance = (
            IndiaRelevanceEngine()
        )


        self.technology_relevance = (
            TechnologyRelevanceEngine()
        )

        self.world_relevance = (
            WorldRelevanceEngine()
        )

        self.queue = IntelligenceQueue()

        self.discovery = DiscoveryEngine()

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
            tuple[
                IntelligenceStory,
                StoryScore,
                PriorityDecision,
                IntelligenceDeliveryDecision,
            ]
        ] = []

        for item in merged:
            item.story.entities = (
                self.entity_extractor.extract(
                    item.story.title,
                    item.story.summary,
                )
            )

            selection = self.selector.evaluate(
                item.story
            )

            geographic = (
    self.geographic_engine.evaluate(
        story=item.story,
        current_location=current_location,
        important_places=important_places,
    )
)

            india = self.india_relevance.evaluate(
                item.story
            )

            technology = (
                self.technology_relevance.evaluate(
                    item.story
                )
            )

            world = (
                self.world_relevance.evaluate(
                    item.story
                )
            )

            total_relevance_bonus = (
                selection.bonus
                + geographic.bonus
                + india.bonus
                + technology.bonus
                + world.bonus
            )

            item.story.personal_relevance = min(
                100,
                item.story.personal_relevance
                + total_relevance_bonus,
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

            if decision.priority in {
                IntelligencePriority.IMPORTANT,
                IntelligencePriority.INTERESTING,
            }:
                self.queue.add(
                    item.story,
                    decision.priority,
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

    def get_discovery_candidates(
        self,
        limit: int = 3,
    ):
        """Return queued stories worth considering as discoveries."""

        pending = self.queue.get_pending(
            limit=10
        )

        candidates = self.discovery.evaluate(
            pending
        )   

        return candidates[:limit]
    
    def record_feedback(
        self,
        story: IntelligenceStory,
        feedback_type: str,
    ) -> None:
        """Record user feedback about an intelligence story."""

        self.feedback_handler.record_story_feedback(
            story=story,
            feedback_type=feedback_type,
        )

    