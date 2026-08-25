from dataclasses import dataclass

from intelligence.models import IntelligenceStory


@dataclass
class WorldRelevance:
    """Global relevance contribution."""

    bonus: int
    reasons: list[str]


class WorldRelevanceEngine:
    """
    Determines whether a world story is important enough
    to receive additional relevance.
    """

    WORLD_CATEGORIES = {
        "world",
        "business",
        "company",
        "science",
        "research",
        "ai",
        "technology",
    }

    def evaluate(
        self,
        story: IntelligenceStory,
    ) -> WorldRelevance:
        """Calculate world-story relevance."""

        if story.location_name:
            location = (
                story.location_name
                .strip()
                .lower()
            )

            known_local_or_india = {
                "jalandhar",
                "punjab",
                "delhi",
                "india",
            }

            if location in known_local_or_india:
                return WorldRelevance(
                    bonus=0,
                    reasons=[],
                )

        if story.category.lower() not in self.WORLD_CATEGORIES:
            return WorldRelevance(
                bonus=0,
                reasons=[],
            )

        bonus = 0
        reasons: list[str] = []

        # Normal world story
        if story.importance >= 70:
            bonus += 20
            reasons.append(
                "significant world development"
            )

        # Major world story
        if story.importance >= 85:
            bonus += 25
            reasons.append(
                "major global importance"
            )

        # Serious global event
        if story.severity >= 70:
            bonus += 25
            reasons.append(
                "high global severity"
            )

        # Time-sensitive global event
        if story.urgency == "immediate":
            bonus += 30
            reasons.append(
                "immediate global urgency"
            )

        return WorldRelevance(
            bonus=min(bonus, 80),
            reasons=reasons,
        )