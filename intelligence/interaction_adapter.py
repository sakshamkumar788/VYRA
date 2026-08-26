from datetime import datetime

from intelligence.delivery import (
    IntelligenceDeliveryDecision,
)
from intelligence.discovery import (
    DiscoveryCandidate,
    DiscoveryEngine,
)
from intelligence.models import IntelligenceStory
from intelligence.priority import IntelligencePriority
from interaction.engine import InteractionEngine
from interaction.policy import (
    InteractionContext,
    InteractionDecision,
    InteractionEvent,
    InteractionPriority,
)

from intelligence.delivery import (
    IntelligenceDeliveryDecision,
)
from intelligence.models import IntelligenceStory
from interaction.policy import (
    InteractionEvent,
    InteractionPriority,
)


class IntelligenceInteractionAdapter:
    """Convert intelligence decisions into interaction events."""

    def create_discovery_event(
        self,
        candidate: DiscoveryCandidate,
    ) -> InteractionEvent:
        """
        Convert a discovery candidate into an InteractionEvent.

        Important discoveries map to HIGH priority.
        Interesting discoveries map to NORMAL priority.
        """

        if candidate.priority == IntelligencePriority.IMPORTANT:
            priority = InteractionPriority.HIGH
        else:
            priority = InteractionPriority.NORMAL

        title = candidate.story.title.strip()

        event_type = (
            f"discovery:{candidate.story.url or title.lower()}"
        )

        return InteractionEvent(
            event_type=event_type,
            message=(
                "I found something you might find interesting: "
                f"{title}"
            ),
            priority=priority,
        )

    def evaluate_discovery(
        self,
        candidate: DiscoveryCandidate,
        interaction_engine: InteractionEngine,
        context: InteractionContext,
    ) -> InteractionDecision:
        """
        Ask the existing InteractionEngine whether
        the discovery should be spoken now.
        """

        event = self.create_discovery_event(
            candidate
        )

        return interaction_engine.evaluate(
            event,
            context,
        )

    def deliver_discovery(
        self,
        candidate: DiscoveryCandidate,
        interaction_engine: InteractionEngine,
        discovery_engine: DiscoveryEngine,
        current_time: datetime,
    ) -> None:
        """
        Record a discovery after it was actually delivered.
        """

        event = self.create_discovery_event(
            candidate
        )

        interaction_engine.record_proactive_interaction(
            event,
            current_time,
        )

        discovery_engine.mark_discovered(
            candidate.story
        )