from dataclasses import dataclass

from intelligence.priority import (
    IntelligencePriority,
    PriorityDecision,
)


@dataclass
class IntelligenceDeliveryDecision:
    """Final decision about when an intelligence story may be surfaced."""

    should_surface: bool
    action: str
    reason: str


class IntelligenceDeliveryPolicy:
    """
    Converts an intelligence priority into a delivery recommendation.

    This layer does not directly speak.
    The existing VYRA InteractionEngine remains responsible for
    the final speak/wait decision.
    """

    def evaluate(
        self,
        decision: PriorityDecision,
    ) -> IntelligenceDeliveryDecision:
        """Determine whether a story is eligible for delivery."""

        if decision.priority == IntelligencePriority.URGENT:
            return IntelligenceDeliveryDecision(
                should_surface=True,
                action="interrupt_candidate",
                reason=(
                    "Story is urgent and should be considered "
                    "for immediate delivery."
                ),
            )

        if decision.priority == IntelligencePriority.IMPORTANT:
            return IntelligenceDeliveryDecision(
                should_surface=True,
                action="next_opportunity",
                reason=(
                    "Story is important and should be delivered "
                    "when the user is receptive."
                ),
            )

        if decision.priority == IntelligencePriority.INTERESTING:
            return IntelligenceDeliveryDecision(
                should_surface=True,
                action="save_for_later",
                reason=(
                    "Story is interesting but should not "
                    "interrupt normal activity."
                ),
            )

        if decision.priority == IntelligencePriority.ON_DEMAND:
            return IntelligenceDeliveryDecision(
                should_surface=False,
                action="on_demand",
                reason=(
                    "Story should be available when the user asks."
                ),
            )

        return IntelligenceDeliveryDecision(
            should_surface=False,
            action="ignore",
            reason="Story is not useful enough to surface.",
        )