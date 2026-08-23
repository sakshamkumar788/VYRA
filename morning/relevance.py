from dataclasses import dataclass

from morning.context import MorningBriefingContext


@dataclass
class BriefingCandidate:
    """A possible piece of information for the briefing."""

    topic: str
    content: str
    score: int
    reason: str


class BriefingRelevanceSelector:
    """
    Selects the most useful information for a briefing.

    This is deliberately deterministic for now.
    Later, richer context/ML can improve the scoring.
    """

    MAX_SELECTED_ITEMS = 4

    def select(
        self,
        context: MorningBriefingContext,
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
            candidates.append(
                BriefingCandidate(
                    topic="news",
                    content=news_item,
                    score=40,
                    reason="Potentially useful current information",
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
        # Novelty suppression
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