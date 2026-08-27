from dataclasses import dataclass
from datetime import datetime

from intelligence.fun_facts import FunFact, FunFactEngine
from intelligence.feedback import FeedbackProfile
from intelligence.discovery_policy import DiscoveryPolicy
from interaction.policy import (
    InteractionEvent,
    InteractionPriority,
    InteractionDecision,
)
from interaction.engine import InteractionEngine
from interaction.policy import InteractionContext


@dataclass
class FunFactCandidate:
    fact: FunFact
    score: int
    reason: str


class FunFactSelector:
    def __init__(
        self,
        fun_fact_engine: FunFactEngine,
        feedback_profile: FeedbackProfile | None = None,
        discovery_policy: DiscoveryPolicy | None = None,
    ) -> None:
        self.fun_fact_engine = fun_fact_engine
        self.feedback_profile = feedback_profile or FeedbackProfile()
        self.discovery_policy = discovery_policy or DiscoveryPolicy()

    def _personalization(self, fact: FunFact) -> int:
        bonus = self.feedback_profile.category_bonus(fact.category)
        # Bound personalization
        return max(-15, min(15, bonus))

    def _score(self, fact: FunFact) -> int:
        base = fact.confidence // 2
        personal = self._personalization(fact)
        # Personalization does not dominate base confidence
        total = base + personal
        return total

    def select(self, category: str | None = None) -> FunFactCandidate | None:
        fact = self.fun_fact_engine.select(category)
        if not fact:
            return None

        score = self._score(fact)
        reason = f"confidence {fact.confidence}, category bonus applied"
        return FunFactCandidate(fact=fact, score=score, reason=reason)

    def can_surface(self, current_time: datetime) -> bool:
        return self.discovery_policy.fun_fact_allowed(current_time)

    def evaluate_interaction(
        self,
        candidate: FunFactCandidate,
        interaction_engine: InteractionEngine,
        context: InteractionContext,
    ) -> InteractionDecision:
        event = InteractionEvent(
            event_type="fun_fact",
            message=f"Random thought: {candidate.fact.text}",
            priority=InteractionPriority.LOW,
        )
        return interaction_engine.evaluate(event, context)

    def record_delivery(self, current_time: datetime) -> None:
        self.discovery_policy.record_discovery(current_time)
