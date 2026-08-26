import re
from dataclasses import dataclass, field

from morning.context import MorningBriefingContext

from intelligence.feedback import FeedbackProfile


@dataclass
class BriefingCandidate:
    """A possible piece of information for the briefing."""

    topic: str
    content: str
    score: int
    reason: str
    category: str | None = None
    entities: list[str] = field(default_factory=list)
    source: str | None = None


class BriefingRelevanceSelector:
    """
    Selects the most useful information for a briefing.

    This is deliberately deterministic for now.
    Later, richer context/ML can improve the scoring.
    """

    MAX_SELECTED_ITEMS = 4

    def _feedback_adjustment(
        self,
        candidate: BriefingCandidate,
        profile: FeedbackProfile | None,
    ) -> int:
        if not profile:
            return 0

        adjustment = 0

        if candidate.category:
            adjustment += profile.category_bonus(candidate.category)

        if candidate.entities:
            seen = set()
            entity_total = 0
            for name in candidate.entities:
                key = name.strip().lower()
                if key in seen:
                    continue
                seen.add(key)
                entity_total += profile.entity_bonus(key)
            adjustment += entity_total

        if candidate.source:
            adjustment += profile.source_bonus(candidate.source.strip().lower())

        # Bound total feedback contribution
        return max(-15, min(15, adjustment))

    def select(
        self,
        context: MorningBriefingContext,
        feedback_profile: FeedbackProfile | None = None,
    ) -> list[BriefingCandidate]:
        """Return the most relevant current briefing candidates."""

        candidates: list[BriefingCandidate] = []

        # ---------------------------------------------------------
        # Tasks
        # ---------------------------------------------------------

        for task in context.important_tasks:
            score = 60

            if "7 PM" in task or "19:00" in task:
                score += 10

            candidates.append(
                BriefingCandidate(
                    topic="task",
                    content=task,
                    score=score,
                    reason="Important scheduled task",
                )
            )

        # ---------------------------------------------------------
        # Important events
        # ---------------------------------------------------------

        for event in context.important_events:
            candidates.append(
                BriefingCandidate(
                    topic="event",
                    content=event,
                    score=80,
                    reason="Upcoming important event",
                )
            )

        # ---------------------------------------------------------
        # Weather
        # ---------------------------------------------------------

        if context.weather:
            candidates.append(
                BriefingCandidate(
                    topic="weather",
                    content=context.weather,
                    score=50,
                    reason="Useful current-day context",
                )
            )

        # ---------------------------------------------------------
        # News
        # ---------------------------------------------------------

        for news_item in context.news_items:
            source = None
            # Try to extract source from "Title (Source)" format
            m = re.search(r"\(([^()]+)\)\s*$", news_item)
            if m:
                source = m.group(1).strip()

            candidates.append(
                BriefingCandidate(
                    topic="news",
                    content=news_item,
                    score=40,
                    reason="Potentially useful current information",
                    source=source,
                )
            )

        # ---------------------------------------------------------
        # Relevant memories
        # ---------------------------------------------------------

        for memory in context.relevant_memories:
            candidates.append(
                BriefingCandidate(
                    topic="memory",
                    content=memory,
                    score=35,
                    reason="Potentially relevant personal context",
                )
            )

        # ---------------------------------------------------------
        # Goals
        # ---------------------------------------------------------

        for goal in context.current_goals:
            candidates.append(
                BriefingCandidate(
                    topic="goal",
                    content=goal,
                    score=45,
                    reason="Current user priority",
                )
            )

        # ---------------------------------------------------------
        # Novelty suppression + feedback adjustment
        # ---------------------------------------------------------

        filtered: list[BriefingCandidate] = []

        for candidate in candidates:
            if (
                candidate.topic
                in context.previously_used_topics
            ):
                candidate.score -= 20

            if (
                candidate.topic
                in context.recently_discussed_topics
            ):
                candidate.score -= 25

            # Apply small personalization adjustment
            adjustment = self._feedback_adjustment(candidate, feedback_profile)
            candidate.score += adjustment

            filtered.append(candidate)

        # ---------------------------------------------------------
        # Highest-value information first
        # ---------------------------------------------------------

        filtered.sort(
            key=lambda item: item.score,
            reverse=True,
        )

        return filtered[
            : self.MAX_SELECTED_ITEMS
        ]