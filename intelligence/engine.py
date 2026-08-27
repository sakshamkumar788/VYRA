from datetime import datetime

from intelligence.discovery import (
    DiscoveryCandidate,
    DiscoveryEngine,
)
from intelligence.interaction_adapter import (
    IntelligenceInteractionAdapter,
)
from interaction.engine import InteractionEngine
from interaction.policy import (
    InteractionContext,
    InteractionDecision,
    InteractionEvent,
    InteractionPriority,
)

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

from intelligence.user_preferences import (
    UserPreferenceManager,
)

from intelligence.feedback import FeedbackProfile

from intelligence.humor import (
    HumorEngine,
    HumorCandidate,
    HumorStyle,
    HumorPolicy,
)


from intelligence.fun_facts import (
    FunFactEngine,
)

from intelligence.fun_fact_selector import (
    FunFactSelector,
    FunFactCandidate,
)

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

        self.humor_engine = HumorEngine()
        self.humor_policy = HumorPolicy()

        self.fun_fact_engine = FunFactEngine()

        self.fun_fact_selector = (
            FunFactSelector(
                fun_fact_engine=self.fun_fact_engine,
                feedback_profile=self.feedback_profile,
            )
        )

        self.user_preferences = (
            UserPreferenceManager(
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

        self.discovery = DiscoveryEngine(
            self.feedback_profile
        )

        from intelligence.current_affairs import CurrentAffairsEngine

        self.current_affairs = CurrentAffairsEngine()

        self.interaction_adapter = (
            IntelligenceInteractionAdapter()
        )

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

    def get_current_affairs(
        self,
        stories: list[IntelligenceStory],
        max_per_section: int = 3,
    ):
        """Build a personalized current-affairs brief."""

        return self.current_affairs.build(
            stories=stories,
            max_per_section=max_per_section,
            feedback_profile=self.feedback_profile,
        )

    def get_fun_fact_candidate(
        self,
        category: str | None = None,
    ) -> FunFactCandidate | None:
        """Return a personalized fun-fact candidate."""

        return self.fun_fact_selector.select(
            category=category,
        )
    
    def evaluate_fun_fact_interaction(
        self,
        candidate: FunFactCandidate,
        interaction_engine: InteractionEngine,
        context: InteractionContext,
    ) -> InteractionDecision:
        """Let the existing InteractionEngine decide whether the fun fact should be spoken."""

        return self.fun_fact_selector.evaluate_interaction(
            candidate,
            interaction_engine,
            context,
        )

    def deliver_fun_fact(
        self,
        candidate: FunFactCandidate,
        current_time: datetime | None = None,
    ) -> None:
        """Record that a fun fact was actually delivered."""

        if current_time is None:
            current_time = datetime.now()

        self.fun_fact_selector.record_delivery(
            current_time,
        )

    def get_humor_candidate(
        self,
        context: str,
        style: str = HumorStyle.PLAYFUL,
    ) -> HumorCandidate | None:
        """Return a humor candidate for the given context."""
        return self.humor_engine.generate(
            context=context,
            style=style,
        )

    def evaluate_humor_interaction(
        self,
        candidate: HumorCandidate,
        interaction_engine: InteractionEngine,
        context: InteractionContext,
    ) -> InteractionDecision:
        """Ask InteractionEngine whether humor should be spoken now."""
        now = context.current_time
        if not self.humor_policy.can_surface(now, context):
            return InteractionDecision.WAIT

        event = InteractionEvent(
            event_type="humor",
            message=candidate.text,
            priority=InteractionPriority.LOW,
        )
        return interaction_engine.evaluate(event, context)

    def deliver_humor(
        self,
        candidate: HumorCandidate,
        interaction_engine: InteractionEngine,
        current_time: datetime | None = None,
    ) -> None:
        """Record actual delivery of humor."""
        if current_time is None:
            current_time = datetime.now()
        event = InteractionEvent(
            event_type="humor",
            message=candidate.text,
            priority=InteractionPriority.LOW,
        )
        interaction_engine.record_proactive_interaction(event, current_time)
        self.humor_policy.record_delivery(current_time)

    def evaluate_discovery(
        self,
        candidate: DiscoveryCandidate,
        interaction_engine: InteractionEngine,
        context: InteractionContext,
    ) -> InteractionDecision:
        """
        Convert a discovery candidate into an InteractionEvent
        and ask the existing InteractionEngine whether to speak.

        This does not mark the story discovered.
        """

        return self.interaction_adapter.evaluate_discovery(
            candidate,
            interaction_engine,
            context,
        )

    def deliver_discovery(
        self,
        candidate: DiscoveryCandidate,
        interaction_engine: InteractionEngine,
        current_time: datetime | None = None,
    ) -> None:
        """
        Record an actually delivered discovery.

        Uses InteractionEngine.record_proactive_interaction()
        and then marks the story discovered.
        """

        if current_time is None:
            current_time = datetime.now()

        self.interaction_adapter.deliver_discovery(
            candidate,
            interaction_engine,
            self.discovery,
            current_time,
        )

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

    
    def apply_user_preference(
        self,
        text: str,
    ) -> bool:
        """
        Parse and apply an explicit user information preference.

        Returns True when the text is recognized as a preference.
        """

        from intelligence.user_preferences import (
            UserPreferenceParser,
        )

        parser = UserPreferenceParser()

        command = parser.parse(
            text
        )

        if command is None:
            return False

        self.user_preferences.apply(
            command
        )

        return True

    