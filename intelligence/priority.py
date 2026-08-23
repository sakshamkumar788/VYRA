from dataclasses import dataclass

from intelligence.scoring import StoryScore


class IntelligencePriority:
    """Possible user-facing priority levels."""

    URGENT = "urgent"
    IMPORTANT = "important"
    INTERESTING = "interesting"
    ON_DEMAND = "on_demand"
    IGNORE = "ignore"


@dataclass
class PriorityDecision:
    """Final behavioral decision for an intelligence story."""

    priority: str
    action: str
    reason: str


class IntelligencePriorityEngine:
    """Converts numerical story scores into VYRA behavior."""

    def decide(
        self,
        score: StoryScore,
    ) -> PriorityDecision:
        """Convert a StoryScore into a behavioral priority."""

        if score.recommended_action == "tell_now":
            return PriorityDecision(
                priority=IntelligencePriority.URGENT,
                action="consider_interrupt",
                reason=score.reason,
            )

        if score.recommended_action == "tell_soon":
            return PriorityDecision(
                priority=IntelligencePriority.IMPORTANT,
                action="tell_at_next_opportunity",
                reason=score.reason,
            )

        if score.recommended_action == "mention_later":
            return PriorityDecision(
                priority=IntelligencePriority.INTERESTING,
                action="save_for_later",
                reason=score.reason,
            )

        if score.recommended_action == "on_demand":
            return PriorityDecision(
                priority=IntelligencePriority.ON_DEMAND,
                action="available_when_asked",
                reason=score.reason,
            )

        return PriorityDecision(
            priority=IntelligencePriority.IGNORE,
            action="ignore",
            reason=score.reason,
        )