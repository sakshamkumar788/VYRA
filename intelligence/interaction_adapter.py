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

    def create_event(
        self,
        story: IntelligenceStory,
        delivery: IntelligenceDeliveryDecision,
    ) -> InteractionEvent | None:
        """
        Convert an intelligence delivery decision into an
        InteractionEvent.

        Returns None when the story should not proactively
        create an interaction.
        """

        if not delivery.should_surface:
            return None

        if delivery.action == "interrupt_candidate":
            priority = InteractionPriority.HIGH

        elif delivery.action == "next_opportunity":
            priority = InteractionPriority.NORMAL

        elif delivery.action == "save_for_later":
            priority = InteractionPriority.LOW

        else:
            return None

        return InteractionEvent(
            event_type=f"intelligence:{story.category}",
            message=story.title,
            priority=priority,
        )