from dataclasses import dataclass

from intelligence.models import IntelligenceStory


@dataclass
class IndiaRelevance:
    """National relevance contribution."""

    bonus: int
    reasons: list[str]


class IndiaRelevanceEngine:
    """Determines whether an India-related story deserves extra weight."""

    IMPORTANT_CATEGORIES = {
        "india",
        "business",
        "company",
        "indian_tech",
        "ai",
        "research",
        "science",
    }

    def evaluate(
        self,
        story: IntelligenceStory,
    ) -> IndiaRelevance:
        """Calculate India-wide relevance."""

        if not story.location_name:
            return IndiaRelevance(
                bonus=0,
                reasons=[],
            )

        location = (
            story.location_name
            .strip()
            .lower()
        )

        if location != "india":
            return IndiaRelevance(
                bonus=0,
                reasons=[],
            )

        bonus = 15
        reasons = ["affects India"]

        if (
            story.category
            in self.IMPORTANT_CATEGORIES
        ):
            bonus += 15
            reasons.append(
                f"important India category: "
                f"{story.category}"
            )

        if story.importance >= 80:
            bonus += 20
            reasons.append(
                "high national importance"
            )

        if story.severity >= 70:
            bonus += 20
            reasons.append(
                "high national severity"
            )

        return IndiaRelevance(
            bonus=bonus,
            reasons=reasons,
        )